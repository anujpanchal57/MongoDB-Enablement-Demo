"""Feature 5 — Atlas Stream Processing with AWS Kinesis Data Streams.

Shows the real connection-registry entries, stream-processor pipelines, and
management commands (from MongoDB's Kinesis announcement + Stream Processing
docs), plus a SIMULATED event flow so the audience can watch IoT telemetry move
through the pipeline — validated, transformed, and routed to a sink or the DLQ.
Nothing here touches a real Kinesis stream, which keeps the demo deterministic.
"""
from __future__ import annotations

from app.models.stream import (
    ScenariosResponse,
    SimulateStreamResponse,
    StreamRecord,
    StreamScenario,
)

DOCS = [
    "https://www.mongodb.com/company/blog/technical/announcing-kinesis-support-for-mongodb-atlas-stream-processing",
    "https://www.mongodb.com/docs/atlas/atlas-stream-processing/manage-stream-processor/",
]

# Connection-registry entries referenced by the pipelines below.
_KINESIS_CONN = {
    "name": "awsKinesis1",
    "type": "Kinesis",
    "aws": {"roleArn": "arn:aws:iam::123456789012:role/atlas-stream-processing"},
    "region": "us-east-1",
}
_ATLAS_CONN = {"name": "atlasCluster", "type": "Cluster", "clusterName": "DemoCluster"}


def _kinesis_to_atlas() -> StreamScenario:
    pipeline = [
        {
            "$source": {
                "connectionName": "awsKinesis1",
                "stream": "device-telemetry",
                "config": {
                    "consumerARN": "arn:aws:kinesis:us-east-1:123456789012:stream/"
                    "device-telemetry/consumer/asp-consumer:1525898737"
                },
            }
        },
        {
            "$validate": {
                "validator": {
                    "$jsonSchema": {
                        "required": ["device_id", "timestamp", "obs"],
                        "properties": {
                            "device_id": {"bsonType": "string", "pattern": "^device_\\d+"},
                            "obs": {
                                "bsonType": "object",
                                "required": ["watts", "temp"],
                                "properties": {
                                    "watts": {"bsonType": "int", "minimum": 0, "maximum": 500},
                                    "temp": {"bsonType": "int"},
                                },
                            },
                        },
                    }
                },
                "validationAction": "dlq",
            }
        },
        {
            "$merge": {
                "into": {"connectionName": "atlasCluster", "db": "iot", "coll": "telemetry"},
                "on": ["device_id"],
            }
        },
    ]
    management = [
        'sp.createStreamProcessor("kinesisToAtlas", pipeline)',
        "sp.kinesisToAtlas.start()",
        "sp.kinesisToAtlas.sample()   // tail live output",
        "sp.kinesisToAtlas.stats()",
        "sp.kinesisToAtlas.stop()",
    ]
    return StreamScenario(
        id="kinesis_to_atlas",
        title="Ingest: AWS Kinesis → transform → MongoDB Atlas",
        direction="kinesis_to_atlas",
        summary="Read IoT telemetry from a Kinesis Data Stream, validate it against a JSON "
        "schema (bad records go to a dead-letter queue), and $merge the rest into Atlas.",
        connections=[_KINESIS_CONN, _ATLAS_CONN],
        pipeline=pipeline,
        management=management,
    )


def _atlas_to_kinesis() -> StreamScenario:
    pipeline = [
        {
            "$source": {
                "connectionName": "atlasCluster",
                "db": "iot",
                "coll": "device_log",
                "config": {"fullDocument": "required"},
            }
        },
        {"$replaceRoot": {"newRoot": "$fullDocument"}},
        {"$match": {"$expr": {"$gte": ["$obs.watts", 100]}}},
        {
            "$emit": {
                "connectionName": "awsKinesis1",
                "stream": "high-load-alerts",
                "partitionKey": "$device_id",
            }
        },
    ]
    management = [
        'sp.createStreamProcessor("atlasToKinesis", pipeline)',
        "sp.atlasToKinesis.start()",
        "sp.atlasToKinesis.sample()",
        "sp.atlasToKinesis.drop()",
    ]
    return StreamScenario(
        id="atlas_to_kinesis",
        title="Egress: MongoDB Atlas change stream → filter → AWS Kinesis",
        direction="atlas_to_kinesis",
        summary="Watch an Atlas collection, keep only high-load device events (watts ≥ 100), "
        "and $emit them to a Kinesis stream partitioned by device.",
        connections=[_ATLAS_CONN, _KINESIS_CONN],
        pipeline=pipeline,
        management=management,
    )


_SCENARIOS = {
    "kinesis_to_atlas": _kinesis_to_atlas,
    "atlas_to_kinesis": _atlas_to_kinesis,
}


def get_scenarios() -> ScenariosResponse:
    return ScenariosResponse(
        title="Atlas Stream Processing with AWS Kinesis Data Streams",
        docs=DOCS,
        scenarios=[_kinesis_to_atlas(), _atlas_to_kinesis()],
    )


def _synth_event(seq: int) -> dict:
    """Deterministically generate a telemetry event. Every 4th event is invalid
    (watts out of the 0–500 range) so the DLQ path is visible in the demo."""
    device_num = seq % 5
    watts = 80 + (seq * 37) % 360  # 80..439 normally
    invalid = seq % 4 == 3
    if invalid:
        watts = 600 + seq  # exceeds schema maximum -> DLQ
    temp = 18 + (seq * 7) % 25
    return {
        "device_id": f"device_{device_num}",
        "timestamp": f"2026-06-15T10:{seq % 60:02d}:00Z",
        "obs": {"watts": watts, "temp": temp},
    }


def simulate(scenario_id: str, count: int) -> SimulateStreamResponse:
    if scenario_id not in _SCENARIOS:
        scenario_id = "kinesis_to_atlas"
    direction = scenario_id
    records: list[StreamRecord] = []
    to_sink = 0
    to_dlq = 0

    for seq in range(count):
        event = _synth_event(seq)
        watts = event["obs"]["watts"]

        if direction == "kinesis_to_atlas":
            # $validate: watts must be within [0, 500], else DLQ.
            if 0 <= watts <= 500:
                records.append(
                    StreamRecord(
                        seq=seq,
                        source=event,
                        output={**event, "_ingestedFrom": "kinesis"},
                        sink="merge:atlas",
                        note="passed schema → $merge into iot.telemetry",
                    )
                )
                to_sink += 1
            else:
                records.append(
                    StreamRecord(
                        seq=seq,
                        source=event,
                        output=None,
                        sink="dlq",
                        note=f"watts={watts} exceeds max 500 → dead-letter queue",
                    )
                )
                to_dlq += 1
        else:  # atlas_to_kinesis: keep watts >= 100, $emit to Kinesis
            if watts >= 100:
                records.append(
                    StreamRecord(
                        seq=seq,
                        source=event,
                        output={"device_id": event["device_id"], "watts": watts},
                        sink="emit:kinesis",
                        note="watts ≥ 100 → $emit to high-load-alerts",
                    )
                )
                to_sink += 1
            else:
                records.append(
                    StreamRecord(
                        seq=seq,
                        source=event,
                        output=None,
                        sink="dlq",
                        note=f"watts={watts} < 100 → filtered out ($match)",
                    )
                )
                to_dlq += 1

    return SimulateStreamResponse(
        scenario_id=scenario_id,
        direction=direction,
        processed=count,
        to_sink=to_sink,
        to_dlq=to_dlq,
        records=records,
    )
