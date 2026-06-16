// MongoDB brand palette (mirrors @leafygreen-ui/palette / mongodb.design).
// Centralised so components share exact brand values.

export const mongo = {
  // Greens
  greenBase: '#00ED64', // signature spring green
  greenDark1: '#00A35C',
  greenDark2: '#00684A',
  greenDark3: '#023430',
  greenLight1: '#71F6BA',
  greenLight2: '#C0FAE6',
  greenLight3: '#E3FCF7',
  // Neutrals
  black: '#001E2B', // brand "black"
  gray900: '#112733',
  gray800: '#1C2D38',
  gray700: '#3D4F58',
  gray500: '#889397',
  gray300: '#C1C7C6',
  gray200: '#E8EDEB',
  gray100: '#F9FBFA',
  white: '#FFFFFF',
  // Accents
  blueBase: '#016BF8',
  purpleBase: '#5E0C9E',
  yellowBase: '#FFC010',
  redBase: '#DB3030',
} as const;

// Per-mode accent colors so each search strategy is visually distinct.
export const modeColor: Record<string, { bg: string; fg: string; accent: string }> = {
  fulltext: { bg: mongo.greenLight3, fg: mongo.greenDark3, accent: mongo.greenDark1 },
  vector: { bg: '#EAF1FF', fg: '#0C2A66', accent: mongo.blueBase },
  hybrid: { bg: '#F3E8FB', fg: mongo.greenDark3, accent: mongo.purpleBase },
};
