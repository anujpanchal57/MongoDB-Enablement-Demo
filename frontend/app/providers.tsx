'use client';

import LeafyGreenProvider from '@leafygreen-ui/leafygreen-provider';
import type { ReactNode } from 'react';

/** Wraps the app in the LeafyGreen provider so MongoDB design-system
 *  components share theme + base font size. Client component by necessity. */
export default function Providers({ children }: { children: ReactNode }) {
  return <LeafyGreenProvider baseFontSize={16}>{children}</LeafyGreenProvider>;
}
