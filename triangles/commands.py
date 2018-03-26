import click
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from triangles.models import Board
from triangles.persistance import Base, Configuration, SeqConf, Sequence, Transformation


DB_FILE = 'triangles.db'


@click.group()
@click.pass_context
@click.option('--dbfile', default='triangles.db', help='Name of the SQLite3 database file')
def cli(ctx, dbfile):
    if ctx.obj is None:
        ctx.obj = {}

    ctx.obj['dbfile'] = dbfile
    ctx.obj['dbengine'] = create_engine('sqlite:///'+ctx.obj['dbfile'])
    ctx.obj['dbsession'] = sessionmaker(bind=ctx.obj['dbengine'])()


# triangle analysis <command> ######################################################################

@cli.group()
def analysis():
    pass


@analysis.command()
@click.pass_context
def findtransformations(ctx):
    """Find solutions that are linear transformations of each other"""

    click.echo('Identifying board configurations that are unique for all valid transformations')
    session = ctx.obj['dbsession']

    # Build the list of unique configurations
    unique_configurations = []
    with click.progressbar(session.query(Configuration).all(),
                           label='   Identifying transformations: ') as bar:
        for working_conf in bar:
            board = Board.from_configuration_id(working_conf.id)
            unique = True

            # If there are unique configurations to check against
            if unique_configurations:
                # For each valid transformation...
                for desc, tx in Board.valid_transformations():
                    matched_conf = check_transformation(board, tx, unique_configurations)

                    if matched_conf:
                        unique = False
                        transformation = Transformation(to_configuration=matched_conf,
                                                        from_configuration=working_conf,
                                                        desc=desc)
                        session.add(transformation)
                    
            if unique:
                unique_configurations.append((working_conf, board))

    session.commit()

    click.echo('{} configurations reduced to {} unique configurations'.format(
        session.query(Configuration).count(), len(unique_configurations)))


def check_transformation(board, tx, unique_configurations):
    t_board = board.copy()
    t_board.transform(tx)

    for unique_conf, unique_board in unique_configurations:
        if t_board == unique_board:
            return unique_conf

    return None


# triangle db <init|drop|reset> ####################################################################

@cli.group()
@click.pass_context
def db(ctx):
    pass


@db.command()
@click.pass_context
def init(ctx):
    """Create the database"""
    click.echo('Initializing the database at {}'.format(ctx.obj['dbfile']))
    engine = ctx.obj['dbengine']
    Base.metadata.create_all(engine)


@db.command()
@click.pass_context
def drop(ctx):
    """Drop the database"""
    click.echo('Dropping all tables in the database at {}'.format(ctx.obj['dbfile']))
    engine = ctx.obj['dbengine']
    Base.metadata.drop_all(engine)


@db.command()
@click.pass_context
def reset(ctx):
    """Drop and create the database"""
    ctx.invoke(drop)
    ctx.invoke(init)


# triangle list <command> ##########################################################################

@cli.group()
def list():
    pass


@list.command()
@click.argument('cid', type=int)
@click.option('--sort/--no-sort', default=True, help='Sort results by sequence id')
@click.option('--unique/--no-unique', default=False,
              help='Return only sequences that do not include transformations')
@click.pass_context
def seqsforconf(ctx, cid, sort, unique):
    """Show sequences for a given configuration"""

    if unique:
        click.echo('Showing only unique sequences')
        click.echo('   ** This will not be accurate if transformations have not been identified')

    session = ctx.obj['dbsession']

    # Get the configuration
    configuration = session.query(Configuration).filter_by(id=cid).one_or_none()
    if not configuration:
        raise click.BadParameter('Configuration {0}, {0:015b} not found'.format(cid))

    # Check for transformations
    transformations = session.query(Transformation).filter_by(to_configuration=configuration).all()
    if transformations:
        click.echo('Configuration {0}, {0:015b} is a transformation of at least one other '
                   'configuration:')

        for tx in transformations:
            click.echo('Transformation {}'.format(tx.desc))
            click.echo('From configuration {0}, {0:015b}'.format(tx.from_configuration_id))
            click.echo(Board.from_configuration_id(tx.from_configuration_id).to_pretty_str())
            click.echo('To configuration {0}, {0:015b}'.format(tx.to_configuration_id))
            click.echo(Board.from_configuration_id(tx.to_configuration_id))

        return
        
    board = Board.from_configuration_id(cid)
    out = 'Listing {0} sequences for configuration {1}, {1:015b}\n'.format(
            configuration.seq_confs.count(), cid) + board.to_pretty_str() + '\n'

    lines = []
    with click.progressbar(configuration.seq_confs.all(), label='Getting data: ') as bar:
        for seq_conf in bar:
            lines.append((
                seq_conf.sequence.id,
                seq_conf.sequence.seq_confs.count(),
                seq_conf.sequence.won
            ))

    if sort:
        click.echo('Sorting results...')
        lines.sort(key=lambda x: x[0])

    with click.progressbar(lines, label='Preparing report: ') as bar:
        for line in bar:
            out_line = '{} ({} moves)'.format(line[0], line[1])
            if line[2]:
                out_line += ' (won)'
            out += out_line + '\n'

    click.echo_via_pager(out) 


# triangle view <configuration|sequence> ###########################################################

@cli.group()
def view():
    pass


@view.command()
@click.argument('cid', type=int)
@click.pass_context
def configuration(ctx, cid):

    session = ctx.obj['dbsession']

    configuration = session.query(Configuration).filter_by(id=cid).one_or_none()

    if not configuration:
        raise click.BadParameter('Configuration {0}, {0:015b} not found'.format(cid))

    board = Board.from_configuration_id(configuration.id)
    click.echo('Configuration {0}: {0:015b}'.format(configuration.id))
    click.echo(board.to_pretty_str(indent=3))


@view.command()
@click.argument('sid', type=int)
@click.pass_context
def sequence(ctx, sid):

    session = ctx.obj['dbsession']

    sequence = session.query(Sequence).filter_by(id=sid).one_or_none()

    if not sequence:
        raise click.BadParameter('Sequence {} could not be found'.format(sid))

    for seq_conf in sequence.seq_confs.order_by(SeqConf.order).all():
        board = Board.from_configuration_id(seq_conf.configuration.id)
        click.echo('Configuration {}: {0:015b}'.format(
            seq_conf.configuration.id, seq_conf.configuration.id))
        click.echo(board.to_pretty_str(indent=3))


# triangle solve ###################################################################################

@cli.command()
@click.option('--empty-position', default=14, help='Starting empty position', type=int)
@click.pass_context
def solve(ctx, empty_position):
    """Brute-force all possitble solutions and save the resulting configurations/sequences to the
    database"""

    # Solve
    click.echo('Finding all feasible solutions with position {} initially empty'.format(
        empty_position))

    boards = [Board(empty_position=empty_position)]
    won_boards = []
    lost_boards = []
    while boards:
        boards, new_won_boards, new_lost_boards = increment_boards(boards)

        if new_won_boards:
            won_boards.extend(new_won_boards)

        if new_lost_boards:
            lost_boards.extend(new_lost_boards)

    # Save
    click.echo('Saving results to the database')
    session = ctx.obj['dbsession']

    save_boards(won_boards, session, won=True)
    save_boards(lost_boards, session, won=False)


def increment_boards(boards):
    """Establish a new list of boards by executing all feasible moves for all boards"""

    new_boards = []
    won_boards = []
    lost_boards = []

    with click.progressbar(boards,
                           label='   Incrementing boards ({:<6}):'.format(len(boards))) as bar:
        for board in bar:

            moves = board.moves()
            if len(moves) < 1:
                lost_boards.append(board)
                continue

            for start, end, jump in moves:
                new_board = board.copy()
                new_board.move(start, end, jump)

                if new_board.is_won():
                    won_boards.append(new_board)
                else:
                    new_boards.append(new_board)

    return new_boards, won_boards, lost_boards


def save_boards(boards, session, won=False):
    with click.progressbar(boards, label='   Saving boards (won={:1}):       '.format(won)) as bar:
        for board in bar:
            # New sequence
            sequence = Sequence(won=won)
            session.add(sequence)

            # Collect boards in order
            sequenced_boards = []
            while board:
                sequenced_boards.append(board)
                board = board.previous_board

            # Find or save each configuration
            for order,board in enumerate(reversed(sequenced_boards)):
                configuration = session.query(Configuration).filter_by(
                                    id=int(str(board),2)).one_or_none()
                if not configuration:
                    configuration = Configuration(id=int(str(board),2), won=board.is_won())
                    session.add(configuration)

                seq_conf = SeqConf(sequence=sequence, configuration=configuration, order=order)
                session.add(seq_conf)

            # Commit everything
            session.commit()
