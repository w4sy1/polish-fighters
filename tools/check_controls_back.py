"""Exercise native F4/touch back plus real fighter movement, attack and AI.

No phone, radio, full campaign or visual performance claim is made by this probe.
"""
import argparse,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--installer',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    common=[str(args.engine.resolve()),'--installer',str(args.installer.resolve()),'--scripts',str(ROOT/'engine/scripts'),
        '--mod',str(ROOT/'engine/scripts/polish-fighters'),'--seed','42','--hub-menu']
    results=[]
    for name,trace in [('f4','*5,4,*5'),('f4-between-samples','*4,4,*6'),('touch-back','*5,@600_20!,@600_20,*5'),('touch-back-between-samples','*4,@600_20!,@600_20,*6')]:
        result=subprocess.run(common+['--mod',str(ROOT/'tools/control-navigation-probe'),'--input-trace',trace],capture_output=True,text=True,timeout=45)
        output=result.stdout+result.stderr;(args.output/(name+'.log')).write_text(output)
        passed=result.returncode==0 and 'screen=characters' in output and 'ready0=false' in output
        results.append(dict(test=name,passed=passed))
        print(name,'PASS' if passed else 'FAIL',flush=True)
    for pack in ['lf4-turbo','polish-originals']:
        result=subprocess.run(common+['--mod',str(ROOT/'content-packs'/pack),'--mod',str(ROOT/'tools/movement-probe'),'--input-trace','*1'],capture_output=True,text=True,timeout=60)
        output=result.stdout+result.stderr;(args.output/(pack+'-movement.log')).write_text(output)
        # 433 is an intentionally stationary summoned turret, not a playable fighter.
        lines=[line for line in output.splitlines() if not line.startswith('433:Sigma_Toaleta:')]
        passed=result.returncode==0 and ':move=' in output and all(':move=false' not in line and ':attack=false' not in line for line in lines)
        results.append(dict(test=pack+'-movement',passed=passed,
            fighters=sum(':move=' in line for line in lines),ai_note='AI observations are logged; not an exhaustive attack/balance assertion'))
        print(pack,'PASS' if passed else 'FAIL',flush=True)
    (args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    return 0 if all(item['passed'] for item in results) else 1

if __name__=='__main__':raise SystemExit(main())
