"""Diagnostic contact sheets and edge crops; originals are never modified."""
import hashlib,json,struct
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/remaining-mechanics-2026-10-30/visual'
def read_image(path):
    try:return Image.open(path).convert('RGB'),None
    except ValueError:
        data=path.read_bytes();offset=struct.unpack_from('<I',data,10)[0]
        header,w,h,planes,bits,codec=struct.unpack_from('<IiiHHI',data,14)
        assert planes==1 and bits==8 and codec==1 and h>0
        palette=[tuple(data[i:i+3][::-1]) for i in range(14+header,offset,4)]
        pixels=bytearray(w*h);x=y=0;pos=offset;seen=set();ended=False
        def put(value):
            nonlocal x
            assert 0<=x<w and 0<=y<h,(path,x,y)
            pixels[(h-1-y)*w+x]=value;seen.add(y);x+=1
        while pos+1<len(data):
            count,value=data[pos:pos+2];pos+=2
            if count:
                for _ in range(count):put(value)
            elif value==0:x=0;y+=1
            elif value==1:ended=True;break
            elif value==2:
                dx,dy=data[pos:pos+2];pos+=2;x+=dx;y+=dy
            else:
                assert pos+value<=len(data)
                for sample in data[pos:pos+value]:put(sample)
                pos+=value+(value%2)
        assert ended,'RLE stream has no end marker'
        image=Image.frombytes('P',(w,h),bytes(pixels));image.putpalette([c for rgb in palette for c in rgb]+[0]*(768-3*len(palette)))
        return image.convert('RGB'),{'reader':'bounded diagnostic RLE8','encoded_rows':len(seen),'end_marker':ended}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report=[]
    for pack in ('bleach','kate','reinforced'):
        folder=ROOT/'content-packs'/pack
        manifest={v:folder/r for v,r in (line[6:].split('|',1) for line in (folder/'package.manifest').read_text().splitlines() if line.startswith('asset='))}
        audit=json.loads((ROOT/f'validation/native-fixes-2026-10-29/{pack}-layout-audit.json').read_text())
        rows=[]
        for entry in audit['sheet_alerts']:
            if entry['status']!='partial_clipping_remaining':continue
            path=manifest.get(entry['asset']) or manifest[entry['asset'][:-4]+'.png'];raw,decoder=read_image(path)
            panel=Image.new('RGB',(1300,550),'#20242c');draw=ImageDraw.Draw(panel)
            draw.text((12,10),f"{pack} {path.name} {raw.width}x{raw.height} | original / sampled edge crops",fill='white')
            preview=raw.copy();preview.thumbnail((1260,350))
            panel.paste(preview,(12,35))
            # Bottom/right physical edge at actual pixel scale (enlarge small sheets).
            edge=raw.crop((max(0,raw.width-440),max(0,raw.height-145),raw.width,raw.height))
            panel.paste(edge,(12,395))
            outside=entry.get('outside',[])
            draw.text((470,400),f"Out-of-bounds references: {len(outside)}",fill='white')
            for i,ref in enumerate(outside[:7]):
                draw.text((470,420+i*17),str({k:ref[k] for k in ('object','frame','picture','rect','fully_empty') if k in ref}),fill='white')
            rows.append(panel)
            report.append({'pack':pack,'asset':entry['asset'],'physical_path':str(path),'size':list(raw.size),'decoder':decoder,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'outside':outside})
        canvas=Image.new('RGB',(1300,550*len(rows)))
        for i,row in enumerate(rows):canvas.paste(row,(0,i*550))
        canvas.save(OUT/(pack+'-contact.png'))
    (OUT/'sheets.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Prepared',len(report),'unchanged source sheets')
if __name__=='__main__':main()
