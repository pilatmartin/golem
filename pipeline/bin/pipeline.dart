import 'dart:convert';
import 'dart:io';

import 'package:collection/collection.dart';
import 'package:csv/csv.dart';
import 'package:pipeline/fasta.dart';
import 'package:pipeline/fasta_generator.dart';
import 'package:pipeline/fasta_validator.dart';
import 'package:pipeline/gff.dart';
import 'package:pipeline/organisms/organism_factory.dart';
import 'package:pipeline/tpm.dart';
import 'package:pipeline/tpm_summary_generator.dart';

void main(List<String> arguments) async {
  if (arguments.isEmpty || arguments.length > 2) {
    throw ArgumentError('Invalid number of arguments.\n\nUsage: dart pipeline.dart <directory> [--with-tss]');
  }
  final organismFolderName = arguments[0];
  final organism = OrganismFactory.getOrganism(organismFolderName);
  final useTss = arguments.contains('--with-tss');
  final noComments = arguments.contains('--no-comments');

  // Find files
  print('Searching input data for `${organism.name}`. TSS: $useTss');
  final inputFilesConfiguration = await BatchConfiguration.fromPath('source_data/$organismFolderName');
  print(' - fasta file: `${inputFilesConfiguration.fastaFile.path}`');
  print(' - gff file: `${inputFilesConfiguration.gffFile.path}`');
  for (final tpmFile in inputFilesConfiguration.tpmFiles) {
    print(' - tpm file: `${tpmFile.path}`');
  }

  // Create output directory, if not exists
  final outputPath = 'output';
  Directory(outputPath).createSync();

  // Load gff file
  final gff = await Gff.fromFile(
    inputFilesConfiguration.gffFile,
    ignoredFeatures: organism.ignoredFeatures,
    triggerFeatures: organism.triggerFeatures,
    transcriptParser: organism.transcriptParser,
    fallbackTranscriptParser: organism.fallbackTranscriptParser,
    seqIdTransformer: organism.seqIdTransformer,
  );
  print('Loaded `${inputFilesConfiguration.gffFile.path}` with ${gff.genes.length} genes');
  print(' - ${gff.genes.where((g) => g.startCodon() != null).length} with start_codon');
  print(' - ${gff.genes.where((g) => g.fivePrimeUtr() != null).length} with five_prime_UTR');
  print(' - ${gff.genes.where((g) => g.threePrimeUtr() != null).length} with three_prime_UTR');

  // Load fasta file
  print('Loading `${inputFilesConfiguration.fastaFile.path}`. This may take a while...');
  final fasta = await Fasta.load(inputFilesConfiguration.fastaFile);
  print(
      'Loaded fasta file `${inputFilesConfiguration.fastaFile.path}` with ${fasta.availableSequences.length} sequences');

  // Load tpm files
  Map<String, Tpm> stagesTpm = {};
  for (final tpmFile in inputFilesConfiguration.tpmFiles) {
    final tpmKey = organism.stageNameFromTpmFilePath(tpmFile.path);
    if (tpmKey == null) {
      print(' - Ignoring file `${tpmFile.path}`');
      continue;
    }
    try {
      final tpmData = await Tpm.fromFile(
        entity: tpmFile,
        geneIdParser: organism.sequenceIdentifier,
      );
      stagesTpm[tpmKey] = tpmData;
      print('Loaded tpm file `${tpmFile.path}` as `$tpmKey` with ${tpmData.genes.length} genes');
    } on FormatException catch (error) {
      print('Error loading tpm file `${tpmFile.path}`: ${error.message}');
    } on FileSystemException catch (error) {
      print('Error loading tpm file `${tpmFile.path}`: ${error.message}');
    } on StateError catch (error) {
      print('Error loading tpm file `${tpmFile.path}`: ${error.message}');
    }
  }

  // Validate data
  final validator = FastaValidator(
    gff: gff,
    fasta: fasta,
    stagesTpm: stagesTpm,
    useTss: useTss,
    allowMissingStartCodon: organism.allowMissingStartCodon,
    oneTranscriptPerGene: organism.oneTranscriptPerGene,
  );
  await validator.validate();

  // Print validation results
  print('Validation results:');
  print(' - total genes: ${gff.genes.length}');
  print(' - valid genes: ${gff.genes.where((g) => g.errors!.isEmpty).length}');
  for (final errorType in ValidationErrorType.values) {
    print(
        ' - error ${errorType.name}: ${gff.genes.where((g) => g.errors!.where((e) => e.type == errorType).isNotEmpty).length}');
  }

  // Save validation results
  final validationOutputFile = File('$outputPath/$organismFolderName${useTss ? '-with-tss' : ''}.errors.csv');
  final errors = [
    ['gene_id', 'errors'],
    for (final gene in gff.genes)
      if (gene.errors!.isNotEmpty) [gene.transcriptId, gene.errors!.map((e) => e.message).join(' | ')],
  ];
  validationOutputFile.writeAsStringSync(ListToCsvConverter().convert(errors));
  print('Wrote errors to `${validationOutputFile.path}`');

  // Save Gene TPM CSV
  final geneTpm = TPMSummaryGenerator(gff, stagesTpm).toCsv();
  final geneTpmOutputFile = File('$outputPath/$organismFolderName${useTss ? '-with-tss' : ''}.validated-genes-tpm.csv');
  geneTpmOutputFile.writeAsStringSync(ListToCsvConverter().convert(geneTpm));
  print('Wrote validated genes TPM to `${geneTpmOutputFile.path}`');

  // Save the output fasta file
  final fastaOutputFile = File('$outputPath/$organismFolderName${useTss ? '-with-tss' : ''}.fasta');
  final metadataOutputFile = File('$outputPath/$organismFolderName${useTss ? '-with-tss' : ''}.metadata.json');
  final fastaSink = fastaOutputFile.openWrite(mode: FileMode.writeOnly);
  final generator = FastaGenerator(
    gff,
    fasta,
    stagesTpm,
    useTss: useTss,
    useSelfInsteadOfStartCodon: organism.useSelfInsteadOfStartCodon,
    useAtg: organism.useAtg,
  );
  
  final metadataResult = <String, dynamic>{};

  await for (final gene in generator.toFasta(organism.deltaBases)) {
    if (noComments) {
      fastaSink.writeln(gene.where((line) => !line.startsWith(';')).join('\n'));
      metadataResult.addAll(toJson(gene));
    } else {
      fastaSink.writeln(gene.join("\n"));
    }
  }

  if (noComments) {
    final encoder = JsonEncoder.withIndent('  ');
    final jsonString = encoder.convert(metadataResult);

    await metadataOutputFile.writeAsString(jsonString);
    print('Wrote json to `${metadataOutputFile.path}`');
  }

  await fastaSink.flush();
  await fastaSink.close();
  
  print('Wrote fasta to `${fastaOutputFile.path}`');
  await fasta.cleanup();
  print('Cleaned up temporary files');

  exit(0);
}

Map<String, dynamic> toJson(List<String> metadataLines) {
  final source = getMetadataLine(metadataLines, ';SOURCE');
  final description = getMetadataLine(metadataLines, ';DESCRIPTION');
  final markers = getMetadataLine(metadataLines, ';MARKERS');
  final transcriptionRates =
      getMetadataLine(metadataLines, ';TRANSCRIPTION_RATES');
  final transcriptId = RegExp(r'^>([^\s]*)').firstMatch(metadataLines[0])!.group(1);

  return {
    transcriptId!: {
      'source': source,
      'description': description,
      'markers': markers != null ? jsonDecode(markers) : null,
      'transcriptionRates':
          transcriptionRates != null ? jsonDecode(transcriptionRates) : null,
    }
  };
}

String? getMetadataLine(List<String> metadataLines, String lineKey) {
  return metadataLines
      .firstWhereOrNull((line) => line.startsWith(lineKey))
      ?.split(' ')
      .firstOrNull;
}

/// Holds the paths to the source files
///
/// expect on .fa or .fasta file, one .gff or .gff3 file
/// TPM files should be located in a `TPM` folder inside the given path.
class BatchConfiguration {
  final FileSystemEntity fastaFile;
  final FileSystemEntity gffFile;
  final List<FileSystemEntity> tpmFiles;
  BatchConfiguration({required this.fastaFile, required this.gffFile, required this.tpmFiles});

  /// Scans the given path and creates the configuration object
  static Future<BatchConfiguration> fromPath(String path) async {
    final dir = Directory(path);
    final List<FileSystemEntity> dirEntities = await dir.list().toList();
    final fastaFiles = dirEntities.where((e) => e.path.endsWith('.fa') || e.path.endsWith('.fasta'));
    if (fastaFiles.length != 1) {
      throw StateError('Expected exactly one FASTA file, ${fastaFiles.length} files found.');
    }
    final fastaFile = fastaFiles.first;
    final gffFiles = dirEntities.where((e) => e.path.endsWith('.gff') || e.path.endsWith('.gff3'));
    if (gffFiles.length != 1) {
      throw StateError('Expected exactly one GFF file, ${gffFiles.length} files found.');
    }
    final gffFile = gffFiles.first;
    final tpmDir = Directory('$path/TPM');
    final List<FileSystemEntity> tpmFiles = await tpmDir.list().toList();
    if (tpmFiles.isEmpty) {
      throw StateError('Expected at least one TPM file, ${tpmFiles.length} files found.');
    }
    tpmFiles.sort((a, b) => a.path.compareTo(b.path));
    return BatchConfiguration(fastaFile: fastaFile, gffFile: gffFile, tpmFiles: tpmFiles);
  }
}
