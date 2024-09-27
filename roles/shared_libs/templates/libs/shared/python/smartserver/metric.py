class Metric():
    @staticmethod
    def _formatLabels(labels=None ):
        if labels is not None:
            label_parts = []
            for _key, _value in labels.items():
                label_parts.append("{}=\"{}\"".format(_key, _value))
            labels = ",".join(label_parts)
        return labels

    @staticmethod
    def buildProcessMetric(service, group, value, labels=None ):
        return "service_process{{service=\"{}\",group=\"{}\"{}}} {}".format(service, group, "," + Metric._formatLabels(labels) if labels is not None else "", value)

    @staticmethod
    def buildStateMetric(service, group, type, value, labels=None ):
        return "service_state{{service=\"{}\",group=\"{}\",type=\"{}\"{}}} {}".format(service, group, type, "," + Metric._formatLabels(labels) if labels is not None else "", value)

    @staticmethod
    def buildDataMetric(service, group, type, value, labels=None ):
        return "service_data{{service=\"{}\",group=\"{}\",type=\"{}\"{}}} {}".format(service, group, type, "," + Metric._formatLabels(labels) if labels is not None else "", value)

    @staticmethod
    def buildGenericMetric(name, labels, value ):
        metric = "{}{{".format(name)
        metric += Metric._formatLabels(labels)
        metric += "}} {}".format(value)
        return metric

    @staticmethod
    def buildMetricsResult(metrics):
        return "{}\n".format( "\n".join(metrics) )

