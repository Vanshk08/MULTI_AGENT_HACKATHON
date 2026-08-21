import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDistanceToNow(dateInput: Date | string | number, options?: { addSuffix?: boolean }): string {
  const date = new Date(dateInput);
  if (isNaN(date.getTime())) return 'recently';
  
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  const isPast = diffInSeconds >= 0;
  const absSeconds = Math.abs(diffInSeconds);
  
  let result = '';
  if (absSeconds < 60) {
    return 'just now';
  } else if (absSeconds < 3600) {
    const mins = Math.floor(absSeconds / 60);
    result = `${mins} min${mins > 1 ? 's' : ''}`;
  } else if (absSeconds < 86400) {
    const hours = Math.floor(absSeconds / 3600);
    result = `${hours} hour${hours > 1 ? 's' : ''}`;
  } else if (absSeconds < 2592000) {
    const days = Math.floor(absSeconds / 86400);
    result = `${days} day${days > 1 ? 's' : ''}`;
  } else if (absSeconds < 31536000) {
    const months = Math.floor(absSeconds / 2592000);
    result = `${months} month${months > 1 ? 's' : ''}`;
  } else {
    const years = Math.floor(absSeconds / 31536000);
    result = `${years} year${years > 1 ? 's' : ''}`;
  }

  if (options?.addSuffix) {
    return isPast ? `${result} ago` : `in ${result}`;
  }
  return result;
}

export function format(dateInput: Date | string | number, formatStr?: string): string {
  const date = new Date(dateInput);
  if (isNaN(date.getTime())) return '';

  const pad = (n: number) => n.toString().padStart(2, '0');
  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
  const monthNamesShort = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  const getOrdinal = (n: number) => {
    const s = ['th', 'st', 'nd', 'rd'];
    const v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
  };

  const hours24 = date.getHours();
  const hours12 = hours24 % 12 || 12;
  const ampm = hours24 >= 12 ? 'pm' : 'am';

  if (formatStr === 'EEEE, MMMM do, yyyy') {
    return `${dayNames[date.getDay()]}, ${monthNames[date.getMonth()]} ${getOrdinal(date.getDate())}, ${date.getFullYear()}`;
  }
  if (formatStr === 'MMM d, h:mm a') {
    return `${monthNamesShort[date.getMonth()]} ${date.getDate()}, ${hours12}:${pad(date.getMinutes())} ${ampm}`;
  }

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
}