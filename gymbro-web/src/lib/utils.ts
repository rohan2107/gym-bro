export function toDateInputValue(d = new Date()) {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function formatRelativeDateTime(dateString: string): string {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) {
    return 'Invalid date';
  }
  
  const now = new Date();
  const isSameDay = now.toDateString() === date.toDateString();
  const yesterday = new Date();
  yesterday.setDate(now.getDate() - 1);
  const isYesterday = yesterday.toDateString() === date.toDateString();
  
  const timeString = date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });
  
  if (isSameDay) return `Today at ${timeString}`;
  if (isYesterday) return `Yesterday at ${timeString}`;
  
  const includeYear = date.getFullYear() !== now.getFullYear();
  const formattedDate = date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    ...(includeYear ? { year: 'numeric' } : {}),
  });
  
  return `${formattedDate} at ${timeString}`;
}

export function handleRequestError(err: unknown): string {
  if (typeof navigator !== 'undefined' && !navigator.onLine) {
    return 'Unable to complete request. Please check your internet connection.';
  }
  if (err instanceof Error) {
    return err.message;
  }
  return 'An unexpected error occurred. Please try again.';
}
