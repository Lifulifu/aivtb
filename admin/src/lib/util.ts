
export type ToastData = {
  type?: string,
  message: string;
};

export function scrollToBottom(node: HTMLElement) {
  node.scroll({ top: node.scrollHeight, behavior: 'smooth' });
};