export function translateRiskGroup(value: string | null | undefined) {
  if (value === "High") return "Высокий риск";
  if (value === "Medium") return "Средний риск";
  if (value === "Low") return "Низкий риск";

  return value ?? "-";
}

export function translatePriority(value: string | null | undefined) {
  if (value === "High") return "Высокий";
  if (value === "Medium") return "Средний";
  if (value === "Low") return "Низкий";

  return value ?? "-";
}

export function translateRecommendation(value: string | null | undefined) {
  const map: Record<string, string> = {
    "No Action": "Без действия",
    "Service Recovery Call": "Звонок для восстановления сервиса",
    "International Plan Review": "Пересмотр международного тарифа",
    "Tariff Optimization": "Оптимизация тарифа",

    // старое и новое название, чтобы работали оба варианта
    "Voice Mail Plan Offer": "Предложение голосовой почты",
    "Voice Mail Offer": "Предложение голосовой почты",

    "Retention Discount": "Скидка на удержание",
  };

  if (!value) {
    return "-";
  }

  return map[value] ?? value;
}

export function translateRiskFactor(value: string | null | undefined) {
  const map: Record<string, string> = {
    // варианты из старой логики
    "Customer service calls ≥ 3": "Обращений в поддержку ≥ 3",
    "International plan = Yes": "Подключён международный тариф",
    "High total day charge": "Высокие дневные расходы",
    "High international charge": "Высокие международные расходы",
    "Voice mail plan = No": "Не подключена голосовая почта",
    "No major risk factor": "Нет выраженного фактора риска",
    "High estimated total charge": "Высокие оценочные расходы",

    // варианты из новой ML/rule-based логики
    "Customer service calls >= 3": "Обращений в поддержку ≥ 3",
    "International plan": "Подключён международный тариф",
    "High day charge": "Высокие дневные расходы",
    "No voice mail plan": "Не подключена голосовая почта",
    "Stable customer profile": "Стабильный профиль клиента",
  };

  if (!value) {
    return "-";
  }

  return map[value] ?? value;
}

export function translateSegment(value: string | null | undefined) {
  const map: Record<string, string> = {
    "High Service Contact Customers": "Клиенты с частыми обращениями в поддержку",
    "High Risk High Charge Customers": "Клиенты высокого риска с высокими расходами",
    "International Plan Users": "Клиенты с международным тарифом",
    "High Day Usage Customers": "Клиенты с высоким дневным использованием",
    "High Charge Customers": "Клиенты с высокими расходами",
    "High Churn Risk Customers": "Клиенты с высоким риском оттока",
    "Stable Customer Profile": "Клиенты со стабильным профилем",
  };

  if (!value) {
    return "-";
  }

  return map[value] ?? value;
}

export function translateRecommendationReason(value?: string | null) {
  if (!value) {
    return "-";
  }

  const exactMap: Record<string, string> = {
    "Customer has many service calls; contact the customer to resolve issues.":
      "У клиента много обращений в поддержку; свяжитесь с клиентом, чтобы решить проблему.",

    "Customer uses an international plan; review international tariff conditions.":
      "Клиент использует международный тариф; проверьте условия международного тарифа.",

    "Customer has high day usage; offer a more suitable tariff plan.":
      "У клиента высокое дневное потребление; предложите более подходящий тарифный план.",

    "Customer has no voice mail plan; offer voice mail plan as a retention action.":
      "У клиента не подключена голосовая почта; предложите услугу как действие по удержанию.",

    "Customer has low churn probability; no retention action is required.":
      "У клиента низкая вероятность оттока; действие по удержанию не требуется.",

    "No action required.":
      "Действие не требуется.",
  };

  if (exactMap[value]) {
    return exactMap[value];
  }

  const normalizedValue = value.toLowerCase();

  if (
    normalizedValue.includes("many service calls") ||
    normalizedValue.includes("service calls")
  ) {
    return "У клиента много обращений в поддержку; свяжитесь с клиентом, чтобы решить проблему.";
  }

  if (
    normalizedValue.includes("international plan") ||
    normalizedValue.includes("international tariff") ||
    normalizedValue.includes("international charges")
  ) {
    return "Клиент использует международный тариф; проверьте условия международного тарифа.";
  }

  if (
    normalizedValue.includes("high day usage") ||
    normalizedValue.includes("total day charge") ||
    normalizedValue.includes("day charge")
  ) {
    return "У клиента высокое дневное потребление или высокие дневные расходы; предложите более подходящий тарифный план.";
  }

  if (
    normalizedValue.includes("voice mail plan") ||
    normalizedValue.includes("no voice mail")
  ) {
    return "У клиента не подключена голосовая почта; предложите услугу как дополнительное действие по удержанию.";
  }

  if (
    normalizedValue.includes("low churn probability") ||
    normalizedValue.includes("stable account")
  ) {
    return "У клиента низкая вероятность оттока и стабильный профиль; дополнительных действий не требуется.";
  }

  if (
    normalizedValue.includes("high estimated total charge") ||
    normalizedValue.includes("high total charge")
  ) {
    return "У клиента высокая оценочная сумма расходов; рассмотрите индивидуальное удерживающее предложение.";
  }

  return value;
}