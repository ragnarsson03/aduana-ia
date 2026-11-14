export type NavTabId = 'pasarela' | 'chat' | 'ledger' | 'explicabilidad' | 'canal';

export interface NavTabItem {
  id: NavTabId;
  label: string;
  hasDot?: boolean;
  dotColor?: string;
  badge?: string;
}
