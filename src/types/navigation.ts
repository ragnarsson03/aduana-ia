export type NavTabId = 'pasarela' | 'chat' | 'ledger' | 'explicabilidad' | 'canal' | 'perfil';

export interface NavTabItem {
  id: NavTabId;
  label: string;
  hasDot?: boolean;
  dotColor?: string;
  badge?: string;
}
