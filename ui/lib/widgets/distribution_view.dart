import 'dart:ui';

import 'package:community_charts_flutter/community_charts_flutter.dart' as charts;
import 'package:file_saver/file_saver.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:golem_ui/analysis/analysis_series.dart';
import 'package:golem_ui/analysis/distribution.dart';
import 'package:golem_ui/genes/gene_model.dart';
import 'package:provider/provider.dart';

/// Widget that builds the analysis series distribution graph
class DistributionView extends StatefulWidget {
  final String? focus;
  final bool usePercentages;
  final bool groupByGenes;
  final double? verticalAxisMin;
  final double? verticalAxisMax;
  final double? horizontalAxisMin;
  final double? horizontalAxisMax;
  const DistributionView(
      {Key? key,
      required this.focus,
      required this.usePercentages,
      required this.groupByGenes,
      required this.verticalAxisMin,
      required this.verticalAxisMax,
      required this.horizontalAxisMin,
      required this.horizontalAxisMax})
      : super(key: key);

  @override
  State<DistributionView> createState() => _DistributionViewState();
}

class _DistributionViewState extends State<DistributionView> {
  String? label;
  late final _key = GlobalKey();

  String get leftAxisTitle {
    if (widget.groupByGenes) {
      return widget.usePercentages ? 'Genes [%]' : 'Genes';
    } else {
      return widget.usePercentages ? 'Occurrences [%]' : 'Occurrences';
    }
  }

  String get subtitle {
    if (widget.groupByGenes) {
      return widget.usePercentages
          ? 'Count of genes with motif in given interval as a percentage of total genes selected for the analysis.'
          : 'Count of genes with motif in given interval.';
    } else {
      return widget.usePercentages
          ? 'Count of motif occurrences in given interval as a percentage of total count of motifs found in genes selected for the analysis.'
          : 'Count of motif occurrences in given interval.';
    }
  }

  @override
  Widget build(BuildContext context) {
    final analyses =
        context.select<GeneModel, List<AnalysisSeries>>((model) => model.analyses.where((a) => a.visible).toList());
    if (analyses.isEmpty) {
      return const Center(child: Text('No series enabled'));
    }

    final distributions = analyses.map((a) => a.distribution!).toList();
    const defaultVerticalMin = 0;
    final defaultVerticalMax = _verticalMaximum(distributions);
    final defaultHorizontalMin = distributions.first.min;
    final defaultHorizontalMax = distributions.first.max;

    return Column(
      children: [
        Row(
          children: [
            Expanded(child: Text(subtitle)),
            const SizedBox(width: 16.0),
            TextButton(onPressed: _handleSave, child: const Text('Save PNG')),
          ],
        ),
        Expanded(
          child: RepaintBoundary(
            key: _key,
            child: ColoredBox(
              color: Colors.white,
              child: charts.LineChart(
                [
                  for (final analysis in analyses)
                    charts.Series<DistributionDataPoint, int>(
                      id: analysis.name,
                      data: analysis.distribution!.dataPoints!,
                      domainFn: (DistributionDataPoint point, i) => point.min,
                      measureFn: _measureFn,
                      labelAccessorFn: (DistributionDataPoint point, _) => '<${point.min}; ${point.max})',
                      strokeWidthPxFn: (_, __) => analysis.stroke,
                      seriesColor: widget.focus == null
                          ? charts.ColorUtil.fromDartColor(analysis.color)
                          : widget.focus == analysis.name
                              ? charts.ColorUtil.fromDartColor(analysis.color)
                              : charts.ColorUtil.fromDartColor(Colors.grey.withOpacity(0.1)),
                    ),
                ],
                animate: false,
                primaryMeasureAxis: charts.NumericAxisSpec(
                  renderSpec: const charts.SmallTickRendererSpec(labelStyle: charts.TextStyleSpec(fontSize: 14)),
                  tickProviderSpec: charts.BasicNumericTickProviderSpec(
                    desiredMinTickCount: 10,
                    zeroBound: false,
                    dataIsInWholeNumbers: !widget.usePercentages,
                  ),
                  tickFormatterSpec: charts.BasicNumericTickFormatterSpec(
                      (value) => widget.usePercentages ? '$value%' : '${value?.floor()}'),
                  viewport: charts.NumericExtents(
                      widget.verticalAxisMin ?? defaultVerticalMin, widget.verticalAxisMax ?? defaultVerticalMax ?? 0),
                ),
                domainAxis: charts.NumericAxisSpec(
                    renderSpec: const charts.SmallTickRendererSpec(labelStyle: charts.TextStyleSpec(fontSize: 14)),
                    viewport: charts.NumericExtents(widget.horizontalAxisMin ?? defaultHorizontalMin,
                        widget.horizontalAxisMax ?? defaultHorizontalMax)),
                behaviors: [
                  charts.ChartTitle(leftAxisTitle, behaviorPosition: charts.BehaviorPosition.start),
                  charts.LinePointHighlighter(
                      selectionModelType: charts.SelectionModelType.info,
                      showHorizontalFollowLine: charts.LinePointHighlighterFollowLineType.nearest,
                      showVerticalFollowLine: charts.LinePointHighlighterFollowLineType.nearest),
                  if (distributions.first.alignMarker != null)
                    charts.RangeAnnotation([
                      charts.LineAnnotationSegment(0, charts.RangeAnnotationAxisType.domain,
                          startLabel: distributions.first.alignMarker?.toUpperCase())
                    ]),
                  //              charts.SeriesLegend(position: charts.BehaviorPosition.end),
                ],
              ),
            ),
          ),
        ),
        if (label != null)
          Text(
            label!,
            style: Theme.of(context).textTheme.bodySmall,
          ),
      ],
    );
  }

  Future<void> _handleSave() async {
    final renderObject = _key.currentContext!.findRenderObject();
    final boundary = renderObject as RenderRepaintBoundary;
    final screenshot = await boundary.toImage(pixelRatio: 3);
    final bytes = await screenshot.toByteData(format: ImageByteFormat.png);
    if (bytes == null) return;
    final slideImage = bytes.buffer.asUint8List();
    const filename = 'graph.png';
    debugPrint('Saving $filename (${slideImage.length} bytes)');
    await FileSaver.instance.saveFile(filename, slideImage, 'png', mimeType: MimeType.PNG);
  }

  void _onSelectionChanged(charts.SelectionModel<num> model) {
    final key = model.selectedSeries[0].labelAccessorFn!.call(model.selectedDatum[0].index);
    final value = model.selectedSeries[0].measureFn(model.selectedDatum[0].index);
    setState(() => label = '$key: $value');
  }

  num? _measureFn(DistributionDataPoint point, int? index) {
    if (widget.groupByGenes) {
      return widget.usePercentages ? (point.genesPercent * 100) : point.genesCount;
    } else {
      return widget.usePercentages ? (point.percent * 100) : point.count;
    }
  }

  num? _verticalMaximum(List<Distribution> distributions) {
    num? max;
    for (final distribution in distributions) {
      for (final point in distribution.dataPoints!) {
        final value = _measureFn(point, null);
        if (max == null || value! > max) {
          max = value;
        }
      }
    }
    return max;
  }
}
