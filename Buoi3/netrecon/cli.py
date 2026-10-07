import json
import click
from engine import ReconEngine, MODES


@click.command()
@click.option('--target', required=True)
@click.option('--ports', default='22,80,443', show_default=True)
@click.option('--mode', type=click.Choice(MODES), default='all')
@click.option('--protocol', type=click.Choice(['tcp', 'udp']), default='tcp')
@click.option('--rate-limit', type=click.FloatRange(.5, 100), default=10.)
@click.option('--subnet', default=None)
@click.option('--technique', type=click.Choice(['connect', 'nmap-connect', 'syn']), default='connect')
@click.option('--email', default='')
@click.option('--output', type=click.Path(dir_okay=False), default=None)
def cli(target, ports, mode, protocol, rate_limit, subnet, technique, email, output):
    try:
        report = ReconEngine().run(target, ports, mode, protocol, rate_limit, subnet, technique, email)
    except (ValueError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc
    text = json.dumps(report, ensure_ascii=False, indent=2)
    click.echo(text)
    if output:
        with open(output, 'w', encoding='utf-8') as handle:
            handle.write(text + '\n')


if __name__ == '__main__':
    cli()
