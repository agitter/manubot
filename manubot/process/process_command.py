import logging
import pathlib


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
    parser.set_defaults(function=cli_process)
    return parser


def cli_process(args):
    args_dict = vars(args)

    # Set paths for content
    content_dir = args.content_directory
    if not content_dir.is_dir():
        logging.warning(f'content directory does not exist: {content_dir}')
    args_dict['citation_tags_path'] = content_dir.joinpath('citation-tags.tsv')
    args_dict['meta_yaml_path'] = content_dir.joinpath('metadata.yaml')
    args_dict['manual_references_path'] = content_dir.joinpath('manual-references.json')

    # Set paths for output
    output_dir = args.output_directory
    output_dir.mkdir(exist_ok=True)
    args_dict['manuscript_path'] = output_dir.joinpath('manuscript.md')
    args_dict['citations_path'] = output_dir.joinpath('citations.tsv')
    args_dict['references_path'] = output_dir.joinpath('references.json')
    args_dict['variables_path'] = output_dir.joinpath('variables.json')

    # Set paths for caching
    args_dict['cache_directory'] = args.cache_directory or output_dir
    args.cache_directory.mkdir(exist_ok=True)
    args_dict['requests_cache_path'] = str(args.cache_directory.joinpath('requests-cache'))

    from manubot.process import prepare_manuscript
    prepare_manuscript(args)