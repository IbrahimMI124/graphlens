"""Build a checksum-verified, whitelisted Phase-5 server handoff using stdlib only.

This packages inputs for fresh server fitting. It never imports model libraries,
installs packages, connects to a server, or includes existing model checkpoints.
"""
import argparse
from contextlib import contextmanager
from importlib import metadata
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import socket
import stat
import sys
import tarfile


RUN_ROOT="runs/phase5-replicated-prepared"
REPORT_OUTPUT="artifacts/phase5/replicated-report"
MANIFEST="artifacts/phase5/work-handoff.json"
REQUIREMENTS="artifacts/phase5/work-requirements.txt"
RESOLVED_FREEZE="artifacts/backend-requirements-resolved.txt"
REVISION="artifacts/pyclause-revision.txt"
JAR="vendor/AnyBURL-23-1x.jar"
JAR_SHA256="d1977ee0ffae3f715e48e32e91e8d46d0c5c243941a5a430fd132086160d06b5"
CONDITIONS=("original","random_global","random_relation_stratified","targeted_local","targeted_relation_matched_control")
SPLITS=("train","valid","test","valid_negatives","test_negatives")
DOCS=("INSTALL","METHODOLOGY","PHASE5","WORK_EXECUTION","STATUS")
SCRIPTS=("run_phase5_work","check_backend_environment","build_phase5_handoff")
REQUIRED_DISTRIBUTIONS={"numpy","torch","pykeen","pandas","scipy","matplotlib","scikit-learn","pytest","pybind11"}


def relative_name(value):
    """One normalized POSIX file name, never an absolute or traversal path."""
    if not isinstance(value,str) or not value or "\\" in value:
        raise ValueError("Archive names must be nonempty relative POSIX paths")
    name=PurePosixPath(value)
    if name.is_absolute() or any(p in ("",".","..") for p in value.split("/")) or str(name)!=value:
        raise ValueError(f"Unsafe relative archive name: {value}")
    return name


def safe_file(project,relative):
    """Reject symlinks in every component and require a regular project file."""
    project=Path(project).resolve(strict=True);name=relative_name(relative);path=project
    for part in name.parts:
        path=path/part
        if path.is_symlink():raise ValueError(f"Symlinks are forbidden in handoffs: {relative}")
    if not path.resolve(strict=True).is_relative_to(project):
        raise ValueError(f"File leaves the project: {relative}")
    if not stat.S_ISREG(path.stat().st_mode):raise ValueError(f"Not a regular file: {relative}")
    return path


@contextmanager
def open_regular(project,relative):
    """Open without following links, including a parent swapped after validation."""
    project=Path(project).resolve(strict=True);name=relative_name(relative)
    safe_file(project,relative)
    directory=os.open(project,os.O_RDONLY|os.O_DIRECTORY)
    file_fd=None
    try:
        for part in name.parts[:-1]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=directory)
            os.close(directory);directory=child
        file_fd=os.open(name.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=directory)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):raise ValueError(f"Not a regular file: {relative}")
        stream=os.fdopen(file_fd,"rb");file_fd=None
        with stream:yield stream
    finally:
        if file_fd is not None:os.close(file_fd)
        os.close(directory)


def file_digest(project,relative):
    digest=hashlib.sha256()
    with open_regular(project,relative) as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):digest.update(block)
    return digest.hexdigest()


def output_path(project,value):
    project=Path(project).resolve(strict=True);value=Path(value)
    path=value if value.is_absolute() else project/value
    try:name=path.relative_to(project).as_posix()
    except ValueError as error:raise ValueError("Handoff outputs must stay inside the project") from error
    relative_name(name)
    current=project
    for part in Path(name).parts:
        current=current/part
        if current.is_symlink():raise ValueError(f"Output symlinks are forbidden: {name}")
    if not path.resolve().is_relative_to(project):raise ValueError("Output leaves the project")
    return path


def atomic_bytes(project,relative,data):
    path=output_path(project,relative);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+f".tmp-{os.getpid()}")
    created=False
    try:
        # Exclusive creation also refuses a stale temporary-file symlink.
        with temporary.open("xb") as stream:
            created=True;stream.write(data)
        os.replace(temporary,path)
    finally:
        if created and temporary.exists() and not temporary.is_symlink():temporary.unlink()


def archive_files(project,files,output):
    """Atomically archive an explicit name→SHA256 mapping; used by tiny tests."""
    project=Path(project).resolve(strict=True);output=output_path(project,output)
    if not files:raise ValueError("Cannot create an empty handoff")
    for name,expected in files.items():
        relative_name(name)
        if not isinstance(expected,str) or not re.fullmatch(r"[0-9a-f]{64}",expected):
            raise ValueError(f"Invalid source SHA256: {name}")
        if safe_file(project,name)==output:raise ValueError("Archive cannot include itself")
        if file_digest(project,name)!=expected:raise ValueError(f"Source changed before archiving: {name}")
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.name+f".tmp-{os.getpid()}")
    created=False
    try:
        with temporary.open("xb") as raw:
            created=True
            with tarfile.open(fileobj=raw,mode="w",format=tarfile.PAX_FORMAT) as archive:
                for name in sorted(files):
                    with open_regular(project,name) as source:
                        properties=os.fstat(source.fileno())
                        member=tarfile.TarInfo(name)
                        member.size=properties.st_size;member.mode=properties.st_mode&0o777
                        member.uid=member.gid=0;member.uname=member.gname="";member.mtime=0
                        archive.addfile(member,source)
            raw.flush();os.fsync(raw.fileno())
        # Validate the actual stored bytes as well as the still-current inputs.
        with tarfile.open(temporary,"r:") as archive:
            members=archive.getmembers()
            if [m.name for m in members]!=sorted(files):raise ValueError("Archive member set/order mismatch")
            for member in members:
                relative_name(member.name)
                if not member.isfile():raise ValueError("Only regular TAR members are allowed")
                stream=archive.extractfile(member);digest=hashlib.sha256()
                for block in iter(lambda:stream.read(1024*1024),b""):digest.update(block)
                stream.close()
                if digest.hexdigest()!=files[member.name]:raise ValueError(f"Archived bytes changed: {member.name}")
        for name,expected in files.items():
            if file_digest(project,name)!=expected:raise ValueError(f"Source changed during archiving: {name}")
        os.replace(temporary,output)
    finally:
        if created and temporary.exists() and not temporary.is_symlink():temporary.unlink()
    checksum=file_digest(project,output.relative_to(project).as_posix())
    atomic_bytes(project,output.relative_to(project).as_posix()+".sha256",f"{checksum}  {output.name}\n".encode())
    return {"archive":str(output),"sha256":checksum,"file_count":len(files)}


def resolved_requirements(text,commit):
    """Keep exact versions and the one public pinned VCS dependency, never paths."""
    if not re.fullmatch(r"[0-9a-f]{40}",commit):raise ValueError("Invalid PyClause revision")
    lines=[];versions={};seen=set();pyclause=False
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith(("#","/","./","../","~")) or re.match(r"^(?:-e|--editable)(?:\s|=)",line) or re.search(r"(?:^|@\s*)file:",line,re.I):
            continue
        if re.match(r"^[A-Za-z]:[\\/]",line):continue
        if re.fullmatch(r"PyClause\s*@\s*git\+https://github\.com/symbolic-kg/PyClause\.git@"+commit,line,re.I):
            name="PyClause";pyclause=True
            keep=f"PyClause @ git+https://github.com/symbolic-kg/PyClause.git@{commit}"
        else:
            match=re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s;#]+)",line)
            if match is None:raise ValueError("Resolved freeze contains an unsupported unpinned or non-public dependency")
            name,version=match.groups()
            if name.lower()=="pyclause":raise ValueError("PyClause must use its pinned public VCS commit")
            versions[name]=version;keep=line
        canonical=re.sub(r"[-_.]+","-",name).lower()
        if canonical in seen:raise ValueError(f"Duplicate dependency in resolved freeze: {name}")
        seen.add(canonical);lines.append(keep)
    if not pyclause:raise ValueError("Resolved freeze lacks the pinned PyClause VCS requirement")
    return "\n".join(lines)+"\n",versions


def collect_sources(project):
    """The complete transfer whitelist; no project-wide catch-all inclusion."""
    project=Path(project).resolve(strict=True);names=set()
    def add(name):safe_file(project,name);names.add(name)
    def tree(pattern):
        count=0
        for path in sorted(project.glob(pattern)):
            relative=path.relative_to(project).as_posix()
            if path.is_symlink():raise ValueError(f"Whitelisted source is a symlink: {relative}")
            if path.is_dir():continue
            if any(p.startswith(".") or p in ("__pycache__","cache","caches") for p in path.relative_to(project).parts):continue
            if path.suffix.lower() in (".pt",".pth",".ckpt"):raise ValueError(f"Checkpoint in transfer inputs: {relative}")
            add(relative);count+=1
        if not count:raise FileNotFoundError(f"No required sources matched {pattern}")
    for pattern in ("kgc/**/*.py","tests/**/*.py","tests/fixtures/**/*","configs/*.json","artifacts/phase5/validation/*"):
        tree(pattern)
    for name in ("pyproject.toml","README.md",JAR,REVISION):add(name)
    for name in DOCS:add(f"docs/{name}.md")
    for name in SCRIPTS:add(f"scripts/{name}.py")
    for split in SPLITS:add(f"data/codex-s/{split}.txt")
    add("data/codex-s/source.json")
    add("runs/next-phase-sparsity-prepared/plan.json")
    for condition in CONDITIONS:
        for filename in ("train.txt","intervention.json"):
            add(f"runs/next-phase-sparsity-prepared/{condition}/{filename}")
    add("runs/next-phase-neural/selection.json")
    selection=json.loads(safe_file(project,"runs/next-phase-neural/selection.json").read_text())
    winner=str(relative_name(selection["winner"]["path"]))
    parts=PurePosixPath(winner).parts
    if len(parts)!=4 or parts[:3]!=("runs","next-phase-neural","search"):
        raise ValueError("Selected recipe must be a configuration directory under the neural search root")
    add(winner+"/curve.json")  # Original configuration/validation bytes; never its PT weights.
    for name in ("runs/next-phase-frozen/mining/training.json","runs/next-phase-frozen/subsets/subsets.json",
                 "runs/next-phase-frozen/subsets/general.rules","runs/next-phase-frozen/subsets/constants.rules"):
        add(name)
    for name in ("protocol.json","native-vocabulary.json","frozen-family-extension.json","preparation.json"):
        add(RUN_ROOT+"/"+name)
    return sorted(names)


def require_pristine_cohort(project):
    root=safe_file(project,RUN_ROOT+"/protocol.json").parent
    for path in root.rglob("*"):
        if path.is_symlink():raise ValueError("Prepared cohort contains a symlink")
        if not path.is_file():continue
        parts=path.relative_to(root).parts
        if path.suffix.lower() in (".pt",".pth",".ckpt") or any(p.startswith(("neural-","rules-")) for p in parts) or path.name=="work-execution.json":
            raise ValueError(f"Prepared cohort already contains attempted/trained cells: {path.relative_to(root)}")
    if (root/"resource-stop.json").exists():raise ValueError("Prepared cohort is resource-stopped")


def build(project_root=None,output="artifacts/phase5/work-handoff.tar"):
    project=Path(project_root or Path(__file__).resolve().parents[1]).resolve(strict=True)
    require_pristine_cohort(project);sources=collect_sources(project)
    if file_digest(project,JAR)!=JAR_SHA256:raise ValueError("AnyBURL JAR differs from the verified fingerprint")
    source=json.loads(safe_file(project,"data/codex-s/source.json").read_text())
    for split in SPLITS:
        if file_digest(project,f"data/codex-s/{split}.txt")!=source["sha256"][split]:
            raise ValueError(f"Official split checksum mismatch: {split}")
    subsets=json.loads(safe_file(project,"runs/next-phase-frozen/subsets/subsets.json").read_text())
    for family in ("general","constants"):
        path=f"runs/next-phase-frozen/subsets/{family}.rules"
        if file_digest(project,path)!=subsets["subsets"][family]["sha256"]:
            raise ValueError(f"Frozen {family} catalog checksum mismatch")
    commit=safe_file(project,REVISION).read_text().strip()
    requirements,locked=resolved_requirements(safe_file(project,RESOLVED_FREEZE).read_text(),commit)
    if not REQUIRED_DISTRIBUTIONS<={re.sub(r"[-_.]+","-",name).lower() for name in locked}:
        raise ValueError("Resolved freeze omits required research/test dependencies")
    for name,expected in locked.items():
        if metadata.version(name)!=expected:raise ValueError(f"Installed distribution differs from resolved freeze: {name}")
    locked["PyClause"]=metadata.version("PyClause")
    direct=json.loads(metadata.distribution("PyClause").read_text("direct_url.json") or "{}")
    if direct.get("vcs_info",{}).get("commit_id")!=commit:
        raise ValueError("Installed PyClause does not certify the pinned VCS revision")
    atomic_bytes(project,REQUIREMENTS,requirements.encode());sources.append(REQUIREMENTS)
    files={name:file_digest(project,name) for name in sorted(sources)}
    manifest={"schema_version":1,"laptop_hostname":socket.gethostname(),"python_version":f"{sys.version_info.major}.{sys.version_info.minor}",
        "lockedversions":dict(sorted(locked.items())),"pyclause_commit":commit,"run_root":RUN_ROOT,"report_output":REPORT_OUTPUT,"files":files}
    atomic_bytes(project,MANIFEST,(json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode())
    archive_inputs={**files,MANIFEST:file_digest(project,MANIFEST)}  # No circular manifest self-hash.
    result=archive_files(project,archive_inputs,output)
    return {**result,"manifest":str(project/MANIFEST),"requirements":str(project/REQUIREMENTS),"training_launched":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root",type=Path)
    parser.add_argument("--output",default="artifacts/phase5/work-handoff.tar")
    args=parser.parse_args();print(json.dumps(build(args.project_root,args.output),sort_keys=True,indent=2))


if __name__=="__main__":main()
