import argparse
from pathlib import Path
from message_encryption import MessageEncryption

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Generate an out-of-band room key, never send it to the relay')
    p.add_argument('output', type=Path)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as handle:
        handle.write(MessageEncryption.generate_key())
    print('Created room key file:', args.output)
