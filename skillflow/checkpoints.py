"""Hybrid panel DAG. The current conversation authors every artifact.

No selector, inference, tension extraction, quality verdict, or synthesis lives
here. The DAG creates only phase boundaries; the session recovers context,
including relevant history, and does the prose work in the room. A newly reached
checkpoint always yields, including when prefilled. Receipts preserve ordering,
not proof of intellectual quality. Old databases retain their original graphs.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys
from datetime import datetime

try:
    from skillflow.dag import Flow, FlowError
    from skillflow.session import format_status, status_summary
    from skillflow.skills import read_shape
except ImportError:  # direct-script execution: import from the enclosing tree
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from skillflow.dag import Flow, FlowError
    from skillflow.session import format_status, status_summary
    from skillflow.skills import read_shape


def _resume_command(session):
    checkout = Path(__file__).resolve().parent.parent / "panel" / "run.sh"
    if checkout.is_file():
        return ["bash", str(checkout), "resume", str(session)]
    return [sys.executable, "-m", "skillflow.checkpoints", "resume",
            str(session)]

SKILLS = ('debate', 'brainstorm', 'review', 'reframe', 'add-skill')


def _custom_shape(skill):
    """Resolve a third-party skill's declared shape from its SKILL.md."""
    root = os.environ.get('SKILLFLOW_SKILLS_ROOT')
    if not root:
        raise ValueError(f'unknown skill {skill!r}')
    shape, error = read_shape(skill, root)
    if error:
        raise ValueError(error)
    return shape


def _custom_stages(skill):
    shape = _custom_shape(skill)
    if shape == 'single':
        return [{'name': 'do', 'artifact': 'final.md', 'round': 0,
                 'prompt': 'Do the work described in SKILL.md for this subject. '
                           'Write final.md as the complete result.'}]
    if shape == 'setup-execute':
        return [{'name': 'setup', 'artifact': 'levelset.md', 'round': 0,
                 'prompt': 'Set up and levelset: read the request and relevant sources, '
                           'state the goal, constraints, and plan. Write levelset.md.'},
                {'name': 'execute', 'artifact': 'final.md', 'round': 0,
                 'prompt': 'Execute the levelset plan. Write final.md as the complete result.'}]
    raise ValueError(f'skill {skill!r} is a prose guide; read its SKILL.md. No phases to run.')


def stages(skill, rounds):
    if skill not in SKILLS:
        return _custom_stages(skill)
    result = [{'name': 'ground', 'artifact': 'ground.md', 'round': 0,
               'prompt': 'Read the request, corrections, and relevant live sources. When prior decisions, rejected approaches, failure modes, or session history could materially change the room, use bounded semantic work-history recall or the supplied history; current instruction and live sources govern. Show the grounding in the conversation. Do not choose the answer.'}]
    def add(name, artifact, prompt, number=0, decision=False):
        result.append(dict(name=name, artifact=artifact, prompt=prompt,
                           round=number, decision=decision))

    if skill == 'add-skill':
        add('draft', 'draft.md',
            'Draft the new SKILL.md text plus the checkpoints.py diff that '
            'registers its stages. Keep the skill thin; the procedure goes '
            'in the graph, never in prose.')
        add('record', 'record.md',
            'Record the validator output, the end-to-end test result, and '
            'the leak-grep result. All three must pass before finalizing.')
        add('finalize', 'final.md',
            'Write the final answer yourself: the new skill, its wiring, '
            'and its proof. The DAG will not summarize for you.')
        return result
    count = rounds if skill in ('debate', 'reframe') else 2
    for n in range(1, count + 1):
        add(f'activate-{n}', f'activation-{n}.md',
            'Choose and read contrasting lens cards in-session. Activate them against this specimen: irritation, evidence, possible move, overreach. Reuse a useful voice; do not force cast rotation.', n)
        if skill == 'debate':
            add(f'round-{n}', f'record-{n}.md',
                'Perform the crossfire in this conversation. Record the exchange, killed or mutated claims, survivors, and unresolved tensions. No conclusion before the collision.', n)
        elif skill == 'brainstorm':
            add(f'round-{n}', 'field.md' if n == 1 else 'record.md',
                'Generate surprising mechanisms through the lenses; preserve the divergent field before judging it.' if n == 1 else
                'Develop, combine, and clarify the field. Prune empty labels, not every unresolved idea. Record mechanisms, touchpoints, first proofs, and questions for later debate.', n)
        elif skill == 'review':
            add(f'round-{n}', 'intent.md' if n == 1 else 'verdict.md',
                'Reconstruct explicit asks, quality bar, corrections, and hard boundaries before judging the work.' if n == 1 else
                'Compare the actual work with intent. Let lenses challenge evidence and each other. Record aligned, intentional_change, miss, and unproven deltas with proof or repair.', n)
        else:
            add(f'field-{n}', f'frames-{n}.md',
                'Generate stronger shapes against the actual build: mechanisms, capability changes, touchpoints, and first proofs. Do not classify yet.', n)
            add(f'lineup-{n}', f'lineup-{n}.md',
                'Now test every surfaced alternative against the current approach. Write the claim/no-claim lineup, cost, blast radius, and cheapest proof.', n)
        if skill in ('debate', 'reframe'):
            add(f'reflect-{n}', f'decision-{n}.json',
                'Judge the round yourself. Write {"action":"continue|finish|refuse","reason":"specific reason"}. Continue only if another round can change the result; otherwise finish. Refuse when the needed evidence or premise is absent. The DAG does not infer this for you.', n, True)
    add('finalize', 'final.md',
        'Write the final answer yourself as the complete useful room: distinct contributions, live exchanges, and the judgment, residual, or next question they earned. Let its shape follow the conversation. Do not replace it with a process report, checklist, or model-selected residue. A refusal remains a refusal. The DAG will not summarize for you.')
    return result


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def rewind(session, target, state=None):
    """Archive affected work and reopen its prerequisite boundary, never erase it."""
    plan = read_json(session / 'checkpoints.json')['stages']
    names = [s['name'] for s in plan]
    if target not in names: raise ValueError(f'unknown repair node: {target}')
    state_path = session / '.checkpoints.json'
    if state is None: state = read_json(state_path)
    start = names.index(target)
    archive = session / 'revisions' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    archive.mkdir(parents=True)
    write_json(archive / 'state.json', state)
    for step in plan[start:]:
        for base in (session, session / 'notes'):
            path = base / step['artifact']
            if path.exists():
                dest = archive / ('notes' if base == session / 'notes' else 'artifacts') / path.name
                dest.parent.mkdir(exist_ok=True)
                path.replace(dest)
        state['accepted'].pop(step['name'], None)
    state['waiting'] = None
    if state.get('stop', {}).get('index', -1) >= start:
        state.pop('stop', None)
    write_json(state_path, state)
    print(f'REOPENED: archived affected work at {archive}. Reopened {target}; resume in this same session.')


def gate(session, name):
    plan = read_json(session / 'checkpoints.json')
    names = [s['name'] for s in plan['stages']]
    index = names.index(name)
    stage = plan['stages'][index]
    state_path = session / '.checkpoints.json'
    state = read_json(state_path) if state_path.exists() else {'accepted': {}, 'waiting': None}
    path = session / stage['artifact']
    actual = digest(path)
    if name in state['accepted']:
        if actual != state['accepted'][name]:
            print(f'error: accepted artifact changed: {path}. Use run.sh rewind <session-dir> {name} to reopen it and invalidate dependent work.', file=sys.stderr)
            return 1
        return 0
    stop = state.get('stop')
    if stop and index > stop['index'] and name != 'finalize':
        print(f'skipped {name}: session chose {stop["action"]}: {stop["reason"]}')
        return 0
    required = names[:index] if not stop else names[:stop['index'] + 1]
    if any(prior not in state['accepted'] for prior in required):
        print(f'error: unmet predecessor for {name}', file=sys.stderr)
        return 1
    if state['waiting'] is None:
        # Refuse to consume prewritten future work as though a pause occurred.
        state['waiting'] = {'name': name, 'prefilled': actual}
        write_json(state_path, state)
        print(f'PAUSE {name}: {stage["prompt"]}\nWrite {path}\nThen resume in this same conversation. This is not a request for human approval.')
        if actual:
            print('This artifact was prefilled before its pause. Reconsider and revise it after this boundary.')
        return 1
    if state['waiting']['name'] != name:
        print('error: checkpoint order mismatch', file=sys.stderr)
        return 1
    if not path.exists() or not path.read_text().strip():
        print(f'PAUSE {name}: missing or empty {path}\n{stage["prompt"]}')
        return 1
    if actual == state['waiting']['prefilled']:
        print(f'PAUSE {name}: prefilled artifact has not been revised after the boundary: {path}')
        return 1
    if stage.get('decision'):
        try:
            choice = read_json(path)
            if not isinstance(choice, dict) or choice.get('action') not in ('continue', 'finish', 'refuse') or not isinstance(choice.get('reason'), str) or not choice['reason'].strip():
                raise ValueError('requires action continue/finish/refuse and a nonempty reason')
        except (ValueError, TypeError) as exc:
            print(f'PAUSE {name}: invalid decision: {exc}')
            return 1
        if choice['action'] != 'continue':
            state['stop'] = dict(choice, index=index)
    notes = session / 'notes'
    notes.mkdir(exist_ok=True)
    (notes / stage['artifact']).write_bytes(path.read_bytes())
    state['accepted'][name] = actual
    state['waiting'] = None
    write_json(state_path, state)
    print(f'recorded {name}: {path} (order only; quality remains the session’s judgment)')
    return 0


def run(session):
    with Flow(str(session / 'skillflow.db')) as flow:
        result = flow.status(flow.run())
    for node in result['nodes']:
        if node.get('output'): print(node['output'].rstrip())
    if result['run']['status'] == 'ok':
        print(f'Complete: session-authored answer at {session / "final.md"}')
        return 0
    print(f'Resume: {shlex.join(_resume_command(session))}')
    return 1


def start_session(skill, subject, rounds, folder, prior=None):
    """Create a session directory, plan, and gate DAG. Returns the path."""
    if not subject.strip(): raise ValueError('subject is empty')
    if skill in SKILLS and not 1 <= rounds <= 8:
        raise ValueError('rounds must be 1-8')
    session = Path(folder).resolve()
    if session.exists() and any(session.iterdir()):
        raise ValueError('session directory is not empty; use resume or a fresh directory')
    session.mkdir(parents=True, exist_ok=True)
    (session / 'subject.txt').write_text(subject + '\n')
    plan = stages(skill, rounds)
    doc = dict(skill=skill, stages=plan)
    if prior is not None:
        prior_final = prior / 'notes' / 'final.md'
        if not prior_final.is_file():
            raise ValueError('prior session has no recorded final.md to chain from')
        (session / 'prior-final.md').write_bytes(prior_final.read_bytes())
        plan[0]['prompt'] += (f'\nPrior linked session ({prior}): read '
                              'prior-final.md in this directory before grounding.')
        doc['prior'] = str(prior)
    write_json(session / 'checkpoints.json', doc)
    with Flow(str(session / 'skillflow.db')) as flow:
        previous = None
        for step in plan:
            name = step['name']
            command = shlex.join([sys.executable, str(Path(__file__).resolve()), '_gate', str(session), name])
            flow.add_node(name, command)
            if previous: flow.add_edge(previous, name)
            previous = name
    return session


USAGE = ('usage: run.sh <debate|reframe> "subject" [rounds] [dir], '
         'run.sh <brainstorm|review|add-skill> "subject" [dir], '
         'run.sh <custom-skill> "subject" [dir], '
         'run.sh resume <dir>, run.sh status <dir>, '
         'run.sh chain <dir> <skill> [rounds] [newdir]')


def main(args=None):
    args = list(sys.argv[1:] if args is None else args)
    try:
        if args and args[0] == '_gate' and len(args) == 3:
            return gate(Path(args[1]), args[2])
        if args and args[0] == 'rewind' and len(args) == 3:
            rewind(Path(args[1]).resolve(), args[2])
            return 0
        if args and args[0] == 'resume' and len(args) == 2:
            session = Path(args[1]).resolve()
            if not (session / 'checkpoints.json').is_file():
                raise ValueError('not a hybrid panel session; resume old graphs with skillflow run in their original directory')
            return run(session)
        if args and args[0] == 'status' and len(args) == 2:
            print(format_status(status_summary(Path(args[1]))))
            return 0
        if args and args[0] == 'chain' and 3 <= len(args) <= 5:
            prior = Path(args[1]).resolve()
            skill = args[2]
            if skill not in SKILLS:
                _custom_shape(skill)
            if not (prior / 'checkpoints.json').is_file():
                raise ValueError('not a hybrid panel session to chain from')
            variable = skill in ('debate', 'reframe')
            rest = args[3:]
            if len(rest) > 2: raise ValueError('too many arguments')
            if rest and variable and rest[0].isdigit():
                rounds, rest = int(rest[0]), rest[1:]
            else:
                rounds = 3
            folder = rest[0] if rest else f'session-{datetime.now():%Y%m%d-%H%M%S-%f}'
            subject = (prior / 'subject.txt').read_text().strip()
            session = start_session(skill, subject, rounds, folder, prior)
            return run(session)
        if len(args) < 2:
            raise ValueError(USAGE)
        skill, subject = args[:2]
        if skill not in SKILLS:
            if _custom_shape(skill) == 'prose':
                root = os.environ.get('SKILLFLOW_SKILLS_ROOT', '.')
                path = Path(root) / skill / 'SKILL.md'
                print(f'skill {skill!r} is a prose guide; read {path}. No phases to run.')
                return 0
            if len(args) > 3: raise ValueError('too many arguments')
            folder = args[2] if len(args) > 2 else f'session-{datetime.now():%Y%m%d-%H%M%S-%f}'
            session = start_session(skill, subject, 0, folder)
            return run(session)
        variable = skill in ('debate', 'reframe')
        if len(args) > (4 if variable else 3): raise ValueError('too many arguments')
        rounds = int(args[2]) if variable and len(args) > 2 else 3
        folder = args[3] if variable and len(args) > 3 else args[2] if not variable and len(args) > 2 else f'session-{datetime.now():%Y%m%d-%H%M%S-%f}'
        session = start_session(skill, subject, rounds, folder)
        return run(session)
    except (ValueError, OSError, FlowError, KeyError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
