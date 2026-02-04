import { metricScope } from "aws-embedded-metrics";
import { config } from "../config";

export const putCountMetric = metricScope((metrics) => async (name: string, value: number) => {
  metrics.setNamespace("CodeQuiz");
  metrics.putMetric(name, value, "Count");
  metrics.putDimensions({ service: config.SERVICE_NAME });
});
