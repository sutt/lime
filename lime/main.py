import argparse
import lime.eval as eval
import lime.grader as grade
import lime.agg as agg
import lime.init as init
import lime.check as check

def main():
    '''
        Dispatch to subcommands
    '''
    
    parser = argparse.ArgumentParser(prog='lime')
    subparsers = parser.add_subparsers(dest='command')

    # Subcommand: eval
    eval_parser = subparsers.add_parser('eval')
    eval.setup_parser(eval_parser)
    eval_parser.set_defaults(func=eval.main)

    # Subcommand: agg
    agg_parser = subparsers.add_parser('agg')
    agg.setup_parser(agg_parser)
    agg_parser.set_defaults(func=agg.main)

    # Subcommand: grade
    grade_parser = subparsers.add_parser('grade')
    grade.setup_parser(grade_parser)
    grade_parser.set_defaults(func=grade.main)

    # Subcommand: init
    init_parser = subparsers.add_parser('init')
    init.setup_parser(init_parser)
    init_parser.set_defaults(func=init.main)

    # Subcommand: check
    check_parser = subparsers.add_parser('check')
    check.setup_parser(check_parser)
    check_parser.set_defaults(func=check.main)

    # Invoke subcommand
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

    return
