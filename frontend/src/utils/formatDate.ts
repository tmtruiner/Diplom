export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "-";
  }

  const normalizedValue = value.includes("T")
    ? value
    : value.replace(" ", "T");

  const date = new Date(normalizedValue);

  if (Number.isNaN(date.getTime())) {
    return value.split(".")[0];
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");

  return `${year}-${month}-${day} ${hours}:${minutes}`;
}