export const countWords = (input: string): number => {
  return input
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .length;
};

export const formatList = (items?: string[]): string => {
  if (!items || items.length === 0) {
    return 'None';
  }
  return items.join(', ');
};
