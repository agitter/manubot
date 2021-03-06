"""
Manubot's command line interface
"""
import argparse
import logging
import pathlib
import sys
import warnings

import manubot
from manubot.util import import_function


def parse_arguments():
    """
    Read and process command line arguments.
    """
    parser = argparse.ArgumentParser(description='Manubot: the manuscript bot for scholarly writing')
    parser.add_argument('--version', action='version', version=f'v{manubot.__version__}')
    subparsers = parser.add_subparsers(
        title='subcommands',
        description='All operations are done through subcommands:',
    )
    # Require specifying a sub-command
    subparsers.required = True  # https://bugs.python.org/issue26510
    subparsers.dest = 'subcommand'  # https://bugs.python.org/msg186387
    add_subparser_process(subparsers)
    add_subparser_cite(subparsers)
    for subparser in subparsers.choices.values():
        subparser.add_argument(
            '--log-level',
            default='WARNING',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Set the logging level for stderr logging',
        )
    args = parser.parse_args()
    return args


def add_subparser_process(subparsers):
    parser = subparsers.add_parser(
        name='process', help='process manuscript content',
        description='Process manuscript content to create outputs for Pandoc consumption. '
                    'Performs bibliographic processing and templating.',
    )
    parser.add_argument(
        '--content-directory', type=pathlib.Path, required=True,
        help='Directory where manuscript content files are located.',
    )
    parser.add_argument(
        '--output-directory', type=pathlib.Path, required=True,
        help='Directory to output files generated by this script.',
    )
    parser.add_argument(
        '--template-variables-path', action='append', default=[],
        help='Path or URL of a JSON file containing template variables for jinja2. '
             'Specify this argument multiple times to read multiple files. '
             'Variables can be applied to a namespace (i.e. stored under a dictionary key) '
             'like `--template-variables-path=namespace=path_or_url`. '
             'Namespaces must match the regex `[a-zA-Z_][a-zA-Z0-9_]*`.',
    )
    parser.add_argument(
        '--cache-directory', type=pathlib.Path,
        help='Custom cache directory. '
             'If not specified, caches to output-directory.',
    )
    parser.add_argument(
        '--clear-requests-cache', action='store_true',
    )
    parser.set_defaults(function='manubot.process.process_command.cli_process')


def add_subparser_cite(subparsers):
    parser = subparsers.add_parser(
        name='cite',
        help='citation to CSL command line utility',
        description='Retrieve bibliographic metadata for one or more citation identifiers.',
    )
    parser.add_argument(
        '--render',
        action='store_true',
        help='Whether to render CSL Data into a formatted reference list using Pandoc. '
             'Pandoc version 2.0 or higher is required for complete support of available output formats.',
    )
    parser.add_argument(
        '--csl',
        default='https://github.com/greenelab/manubot-rootstock/raw/master/build/assets/style.csl',
        help="When --render, specify an XML CSL definition to style references (i.e. Pandoc's --csl option). "
             "Defaults to Manubot's style.",
    )
    parser.add_argument(
        '--format',
        choices=['plain', 'markdown', 'docx', 'html', 'jats'],
        help="When --render, format to use for output file. "
             "If not specified, attempt to infer this from filename extension. "
             "Otherwise, default to plain.",
    )
    parser.add_argument(
        '--output',
        type=pathlib.Path,
        help='Specify a file to write output, otherwise default to stdout.',
    )
    parser.add_argument(
        '--allow-invalid-csl-data',
        dest='prune_csl',
        action='store_false',
        help='Allow CSL Items that do not conform to the JSON Schema. Skips CSL pruning.',
    )
    parser.add_argument(
        'citations',
        nargs='+',
        help='One or more (space separated) citations to produce CSL for.',
    )
    parser.set_defaults(function='manubot.cite.cite_command.cli_cite')


def main():
    """
    Called as a console_scripts entry point in setup.py. This function defines
    the manubot command line script.
    """
    # Track if message gets logged with severity of error or greater
    # See https://stackoverflow.com/a/45446664/4651668
    import errorhandler
    error_handler = errorhandler.ErrorHandler()

    # Log DeprecationWarnings
    warnings.simplefilter('always', DeprecationWarning)
    logging.captureWarnings(True)

    # Log to stderr
    logger = logging.getLogger()
    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setFormatter(logging.Formatter('## {levelname}\n{message}', style='{'))
    logger.addHandler(stream_handler)

    args = parse_arguments()
    logger.setLevel(getattr(logging, args.log_level))

    function = import_function(args.function)
    function(args)

    if error_handler.fired:
        logging.critical('Failure: exiting with code 1 due to logged errors')
        raise SystemExit(1)
