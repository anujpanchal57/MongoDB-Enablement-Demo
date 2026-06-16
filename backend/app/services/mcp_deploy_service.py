"""Feature 3 — guided walkthrough for deploying the MongoDB MCP server to AWS
Bedrock AgentCore Runtime.

The commands shown are the REAL steps from
https://github.com/mongodb-js/mongodb-mcp-server/tree/main/deploy/aws
rendered with the user's config so they are copy-paste ready. "Running" a step
is SIMULATED (no AWS calls), which makes the demo safe and repeatable on stage.
"""
from __future__ import annotations

from app.models.mcp_deploy import DeployConfig, DeployStep, SimulateResponse, StepsResponse

SOURCE_REPO = "https://github.com/mongodb-js/mongodb-mcp-server/tree/main/deploy/aws"

PREREQUISITES = [
    "AWS CLI v2 installed and configured (`aws configure`).",
    "Docker or Finch for building container images.",
    "Permissions for Amazon ECR and Amazon Bedrock AgentCore in the target region.",
    "A reachable MongoDB connection string using the standard mongodb:// scheme "
    "(mongodb+srv:// is not supported by AgentCore).",
]


def _ecr_uri(c: DeployConfig) -> str:
    return f"{c.account_id}.dkr.ecr.{c.region}.amazonaws.com/{c.repo_name}"


def build_steps(c: DeployConfig) -> list[DeployStep]:
    ecr = _ecr_uri(c)
    return [
        DeployStep(
            id="ecr-repo",
            title="Create an ECR repository",
            summary="AgentCore pulls the MCP server image from a private Amazon ECR repository.",
            commands=[f"aws ecr create-repository --repository-name {c.repo_name} --region {c.region}"],
            notes=["Idempotent in practice — skip if the repository already exists."],
            docs=SOURCE_REPO,
        ),
        DeployStep(
            id="ecr-auth",
            title="Authenticate Docker to ECR",
            summary="Log Docker into your private registry so you can push the image.",
            commands=[
                f"aws ecr get-login-password --region {c.region} | \\\n"
                f"  docker login --username AWS --password-stdin {c.account_id}.dkr.ecr.{c.region}.amazonaws.com"
            ],
            docs=SOURCE_REPO,
        ),
        DeployStep(
            id="build",
            title="Build the container image (ARM64)",
            summary="Build the MCP server image from the repo's Dockerfile.",
            commands=[f"docker build --platform linux/arm64 \\\n  -t {ecr}:latest ."],
            notes=["AgentCore requires linux/arm64 — the --platform flag is mandatory."],
            docs=SOURCE_REPO,
        ),
        DeployStep(
            id="push",
            title="Push the image to ECR",
            summary="Upload the built image so AgentCore can deploy it.",
            commands=[f"docker push {ecr}:latest"],
            docs=SOURCE_REPO,
        ),
        DeployStep(
            id="configure",
            title="Create the AgentCore Runtime",
            summary="Point an AgentCore runtime at your image and set the MCP server environment.",
            commands=[
                "aws bedrock-agentcore-control create-agent-runtime \\\n"
                f"  --agent-runtime-name {c.runtime_name} \\\n"
                f"  --region {c.region} \\\n"
                f'  --agent-runtime-artifact \'{{"containerConfiguration": {{"containerUri": "{ecr}:latest"}}}}\' \\\n'
                "  --network-configuration '{\"networkMode\": \"PUBLIC\"}' \\\n"
                "  --protocol-configuration '{\"serverProtocol\": \"MCP\"}'"
            ],
            env={
                "MDB_MCP_CONNECTION_STRING": c.connection_string,
                "MDB_MCP_EXTERNALLY_MANAGED_SESSIONS": "true",
                "MDB_MCP_HTTP_RESPONSE_TYPE": "json",
                "MDB_MCP_DISABLED_TOOLS": "atlas-local",
            },
            notes=[
                "The MCP server listens on port 8000 over HTTP with JSON responses (not SSE).",
                "Set the env vars above on the runtime; the connection string must be mongodb:// .",
            ],
            docs=SOURCE_REPO,
        ),
        DeployStep(
            id="invoke",
            title="Invoke the runtime (list tools)",
            summary="Confirm the MCP server is live by calling the JSON-RPC tools/list method.",
            commands=[
                f'AGENT_ARN="arn:aws:bedrock-agentcore:{c.region}:{c.account_id}:runtime/{c.runtime_name}"\n'
                "ENCODED_ARN=$(python3 -c \"import urllib.parse,os;print(urllib.parse.quote(os.environ['AGENT_ARN'],safe=''))\")\n"
                f'curl -X POST \\\n'
                f'  "https://bedrock-agentcore.{c.region}.amazonaws.com/runtimes/${{ENCODED_ARN}}/invocations?qualifier=DEFAULT" \\\n'
                '  -H "Authorization: Bearer <TOKEN>" \\\n'
                '  -H "Content-Type: application/json" \\\n'
                "  -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}'"
            ],
            docs=SOURCE_REPO,
        ),
        DeployStep(
            id="monitor",
            title="Monitor logs",
            summary="Inspect AgentCore logs in CloudWatch for health and debugging.",
            commands=[
                f'aws logs describe-log-groups --region {c.region} \\\n'
                '  --log-group-name-prefix "/aws/bedrock-agentcore"'
            ],
            docs=SOURCE_REPO,
        ),
    ]


def get_steps(config: DeployConfig) -> StepsResponse:
    return StepsResponse(
        title="Deploy the MongoDB MCP Server on AWS Bedrock AgentCore",
        source_repo=SOURCE_REPO,
        prerequisites=PREREQUISITES,
        steps=build_steps(config),
        config=config,
    )


# Realistic simulated outputs keyed by step id.
def _simulated_output(step_id: str, c: DeployConfig) -> tuple[bool, str]:
    ecr = _ecr_uri(c)
    outputs = {
        "ecr-repo": (
            True,
            "{\n"
            '    "repository": {\n'
            f'        "repositoryArn": "arn:aws:ecr:{c.region}:{c.account_id}:repository/{c.repo_name}",\n'
            f'        "repositoryUri": "{ecr}",\n'
            '        "imageTagMutability": "MUTABLE"\n'
            "    }\n}",
        ),
        "ecr-auth": (True, "Login Succeeded"),
        "build": (
            True,
            f"[+] Building 38.4s (12/12) FINISHED\n => naming to {ecr}:latest  done\n"
            " => exporting to image (linux/arm64)  done",
        ),
        "push": (
            True,
            f"The push refers to repository [{ecr}]\n"
            "latest: digest: sha256:9f2c…e1ab size: 2841\n=> pushed",
        ),
        "configure": (
            True,
            "{\n"
            f'    "agentRuntimeArn": "arn:aws:bedrock-agentcore:{c.region}:{c.account_id}:runtime/{c.runtime_name}",\n'
            f'    "agentRuntimeName": "{c.runtime_name}",\n'
            '    "status": "CREATING"\n}\n'
            "(env applied: MDB_MCP_EXTERNALLY_MANAGED_SESSIONS=true, MDB_MCP_HTTP_RESPONSE_TYPE=json)",
        ),
        "invoke": (
            True,
            '{"jsonrpc":"2.0","id":1,"result":{"tools":['
            '{"name":"find","description":"Query documents in a collection"},'
            '{"name":"aggregate","description":"Run an aggregation pipeline"},'
            '{"name":"list-collections","description":"List collections in a database"},'
            '{"name":"insert-many","description":"Insert documents"}]}}',
        ),
        "monitor": (
            True,
            "{\n"
            '    "logGroups": [\n'
            f'        {{"logGroupName": "/aws/bedrock-agentcore/runtimes/{c.runtime_name}-DEFAULT"}}\n'
            "    ]\n}",
        ),
    }
    return outputs.get(step_id, (False, f"Unknown step: {step_id}"))


def simulate(step_id: str, config: DeployConfig) -> SimulateResponse:
    ok, output = _simulated_output(step_id, config)
    # Deterministic pseudo-duration per step (no wall-clock randomness needed).
    duration = 400 + (sum(ord(ch) for ch in step_id) % 1200)
    return SimulateResponse(
        step_id=step_id, ok=ok, simulated=True, output=output, duration_ms=duration
    )
