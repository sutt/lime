import argparse
from lime.commands.eval import (
    setup_parser as eval_setup_parser,
    main as eval_main,
)
from lime.commands.grade  import (
    setup_parser as grade_setup_parser,
    main as grade_main,
)
from lime.commands.agg  import (
    setup_parser as agg_setup_parser,
    main as agg_main,
)
from lime.commands.initialize  import (
    setup_parser as init_setup_parser,
    main as init_main,
)
from lime.commands.check  import (
    setup_parser as check_setup_parser,
    main as check_main,
)
from lime.commands.render  import (
    setup_parser as render_setup_parser,
    main as render_main,
)

def main():
    '''
        Dispatch to subcommands
    '''
    
    parser = argparse.ArgumentParser(prog='lime')
    subparsers = parser.add_subparsers(dest='command')

    # Subcommand: eval
    eval_parser = subparsers.add_parser('eval')
    eval_setup_parser(eval_parser)
    eval_parser.set_defaults(func=eval_main)

    # Subcommand: agg
    agg_parser = subparsers.add_parser('agg')
    agg_setup_parser(agg_parser)
    agg_parser.set_defaults(func=agg_main)

    # Subcommand: grade
    grade_parser = subparsers.add_parser('grade')
    grade_setup_parser(grade_parser)
    grade_parser.set_defaults(func=grade_main)

    # Subcommand: init
    init_parser = subparsers.add_parser('init')
    init_setup_parser(init_parser)
    init_parser.set_defaults(func=init_main)

    # Subcommand: check
    check_parser = subparsers.add_parser('check')
    check_setup_parser(check_parser)
    check_parser.set_defaults(func=check_main)

    # Subcommand: render
    render_parser = subparsers.add_parser('render')
    render_setup_parser(render_parser)
    render_parser.set_defaults(func=render_main)

    # Invoke subcommand
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

    return

if __name__ == '__main__':
    main()