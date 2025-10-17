import 'styled-components';

declare module 'styled-components' {
  export interface DefaultTheme {
    bg: string;
    nodeBg: string;
    minimapMaskBg: string;
    controlsBg: string;
    controlsColor: string;
    controlsBorder: string;
    isDarkMode?: boolean;
  }
}
