import { nord, spacing, typography } from './tokens';

export const appTheme = {
  color: {
    background: nord.snowStorm[2],
    surface: '#FFFFFF',
    textPrimary: nord.polarNight[0],
    textMuted: nord.polarNight[3],
    border: nord.snowStorm[0],
    primary: nord.frost[3],
    success: nord.aurora.green,
    warning: nord.aurora.yellow,
    danger: nord.aurora.red,
  },
  spacing,
  typography,
};
