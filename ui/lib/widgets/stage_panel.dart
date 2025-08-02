import 'package:collection/collection.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:golem_ui/genes/stage_selection.dart';
import 'package:golem_ui/genes/gene_list.dart';
import 'package:golem_ui/genes/gene_model.dart';
import 'package:golem_ui/utilities/text.dart';
import 'package:provider/provider.dart';
import 'package:truncate/truncate.dart';

/// Widget that is shown just below the panel headline
class StageSubtitle extends StatelessWidget {
  const StageSubtitle({super.key});

  @override
  Widget build(BuildContext context) {
    final selectedStages =
        context.select<GeneModel, List<String>>((model) => model.stageSelection?.selectedStages ?? []);
    final expectedResults = context.select<GeneModel, int>((model) => model.expectedSeriesCount);
    if (expectedResults > 60 && selectedStages.length > 5) {
      return Text('Analysis would result in $expectedResults series, reduce the number of selected stages');
    }
    if (selectedStages.isEmpty) {
      return const Text('No stages selected');
    }
    final isMain = selectedStages.contains(GeneModel.kAllStages);
    final realStages = selectedStages.where((s) => s != GeneModel.kAllStages).toList();
    List<String> texts = [];
    if (isMain) texts.add('Genome');
    if (realStages.isNotEmpty) {
      texts.add(realStages.length == 1 ? realStages.first : '${realStages.length} other stages');
    }
    return Text(texts.join(' and '));
  }
}

/// Widgewt that builds the panel with stage selection
class StagePanel extends StatefulWidget {
  final Function(StageSelection? selection) onChanged;

  const StagePanel({super.key, required this.onChanged});

  @override
  State<StagePanel> createState() => _StagePanelState();
}

class _StagePanelState extends State<StagePanel> {
  final _formKey = GlobalKey<FormState>();

  late List<String> _selectedStages;
  late FilterStrategy? _strategy;
  late FilterSelection? _selection;
  late double? _percentile;
  late int? _count;

  final _percentileController = TextEditingController();
  final _countController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _updateStateFromModel();
  }

  @override
  void dispose() {
    _percentileController.dispose();
    _countController.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant StagePanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.key != widget.key) {
      _updateStateFromModel();
    }
  }

  void _updateStateFromModel() {
    final filter = GeneModel.of(context).stageSelection ?? StageSelection();
    _selectedStages = filter.selectedStages;
    _strategy = filter.strategy;
    _selection = filter.selection;
    _percentile = filter.percentile;
    _count = filter.count;
    _percentileController.text = '${((_percentile ?? 0) * 100).round()}';
    _countController.text = '$_count';
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final allStagesKeys = context.select<GeneModel, List<String>>((model) => model.sourceGenes?.stageKeys ?? []);
    final groupedStagesKeys = groupBy(allStagesKeys, (str) => str.split(' ').first);
    final allowFilter = context.select<GeneModel, bool>((model) => model.sourceGenes?.stages == null);
    final stageColors = context.select<GeneModel, Map<String, Color>>((model) => model.sourceGenes?.colors ?? {});
    final sourceGenes = context.select<GeneModel, GeneList?>((model) => model.sourceGenes);
    if (sourceGenes == null) return const Center(child: Text('Load source data first'));
    return Align(
      alignment: Alignment.topLeft,
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('GENOME', style: textTheme.titleSmall),
            Text('Distribution of the motif across the genome.', style: textTheme.bodySmall),
            const SizedBox(height: 16),
            _StageCard(
              name: 'GENOME',
              color: null,
              isSelected: _selectedStages.contains(GeneModel.kAllStages) == true,
              onToggle: (value) => _handleToggle(GeneModel.kAllStages, value),
            ),
            const SizedBox(height: 16),
            Text('DEVELOPMENTAL STAGES', style: textTheme.titleSmall),
            Text('Distribution of the motif in genes with elevated transcript levels in certain developmental stage.',
                style: textTheme.bodySmall),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final group in groupedStagesKeys.entries)
                  _StageCardList(groupName: group.key, children: [
                    for (final name in group.value)
                      _StageCard(
                          name: name,
                          color: stageColors[name],
                          isSelected: _selectedStages.contains(name),
                          onToggle: (value) => _handleToggle(name, value))
                  ]),
              ],
            ),
            if (allowFilter) ...[
              const SizedBox(height: 16),
              Text('Choose the transcript level based on TPM:', style: textTheme.titleSmall),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                crossAxisAlignment: WrapCrossAlignment.end,
                children: [
                  CupertinoSlidingSegmentedControl<FilterStrategy>(
                    children: const {
                      FilterStrategy.top: Text('Most transcribed'),
                      FilterStrategy.bottom: Text('Least transcribed'),
                    },
                    onValueChanged: (value) {
                      setState(() => _strategy = value!);
                      _handleChanged();
                    },
                    groupValue: _strategy,
                  ),
                  if (_selection == FilterSelection.percentile)
                    SizedBox(
                      width: 200,
                      child: TextFormField(
                        controller: _percentileController,
                        decoration: const InputDecoration(labelText: 'Percentile', suffix: Text('th')),
                        keyboardType: TextInputType.number,
                        onChanged: (value) {
                          setState(() =>
                              _percentile = ((double.tryParse(_percentileController.text) ?? 0) / 100).clamp(0, 1));
                          _handleChanged();
                        },
                        validator: (value) {
                          final parsed = double.tryParse(_percentileController.text);
                          if (parsed == null || parsed < 0 || parsed > 100) return 'Enter a number between 0 and 100';
                          return null;
                        },
                      ),
                    ),
                  if (_selection == FilterSelection.fixed)
                    SizedBox(
                      width: 200,
                      child: TextFormField(
                        controller: _countController,
                        decoration: const InputDecoration(labelText: 'Count'),
                        keyboardType: TextInputType.number,
                        onChanged: (value) {
                          setState(() =>
                              _count = (int.tryParse(_countController.text) ?? 0).clamp(0, sourceGenes.genes.length));
                          _handleChanged();
                        },
                        validator: (value) {
                          final parsed = int.tryParse(_countController.text);
                          if (parsed == null || parsed < 0 || parsed > sourceGenes.genes.length) {
                            return 'Enter a number between 0 and ${sourceGenes.genes.length}';
                          }
                          return null;
                        },
                      ),
                    ),
                  CupertinoSlidingSegmentedControl<FilterSelection>(
                    children: const {
                      FilterSelection.fixed: Text('Genes'),
                      FilterSelection.percentile: Text('Percentile'),
                    },
                    onValueChanged: (value) {
                      setState(() => _selection = value!);
                      _handleChanged();
                    },
                    groupValue: _selection,
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _handleChanged() {
    if (_formKey.currentState!.validate()) {
      _formKey.currentState!.save();
      widget.onChanged(StageSelection(
        selectedStages: _selectedStages,
        strategy: _strategy,
        selection: _selection,
        percentile: _percentile,
        count: _count,
      ));
    } else {
      assert(false);
    }
  }

  void _handleToggle(String key, bool value) {
    setState(() {
      if (value) {
        _selectedStages.add(key);
      } else {
        _selectedStages.remove(key);
      }
    });
    _handleChanged();
  }
}

class _StageCard extends StatelessWidget {
  final String name;
  final Color? color;
  final bool isSelected;
  final Function(bool value) onToggle;
  const _StageCard({required this.name, required this.color, required this.isSelected, required this.onToggle});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final backgroundColor = isSelected ? (color ?? Colors.grey) : (color ?? Colors.grey).withOpacity(0.4);
    final textColor = backgroundColor.computeLuminance() > 0.5 ? Colors.black : Colors.white;
    return SizedBox(
      width: 160,
      height: 120,
      child: Card(
        color: backgroundColor,
        child: InkWell(
          onTap: () => onToggle(!isSelected),
          child: Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  normalizeStageName(name),
                  overflow: TextOverflow.fade,
                  style: textTheme.titleSmall?.copyWith(color: textColor),
                  maxLines: 3,
                ),
                Checkbox(value: isSelected, onChanged: (value) => onToggle(value!))
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _StageCardList extends StatelessWidget {
  final String groupName;
  final List<_StageCard> children;

  const _StageCardList({
    required this.groupName,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
          child: Text(
            normalizeStageName(groupName),
            style: textTheme.titleSmall,
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8.0),
          child: Wrap(
            spacing: 8.0,
            runSpacing: 8.0,
            children: children,
          ),
        ),
      ],
    );
  }
}
