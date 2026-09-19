# -*- coding: utf-8 -*-
import asyncio
import edge_tts
import subprocess

text_full = '刚开口就被秒挂;面是客户的“什天忙　不需要”，大脑一片空陽不知如何回复。新人乏乏异议经验，根本留不住客户，最后导致开单软怎也不去〦'

async def main():
    comm = edge_tts.Communicate(text_full, 'zh-CN-YunjianNeural', rate='+18%')
    submaker = edge_tts.SubMaker()
    with open('output/audio/scene1_clean_voice.mp3', 'wb') as f:
        async for chunk in comm.stream():
            if chunk['type'] == 'audio':
                f.write(chunk['data'])
            elif chunk['type'] == 'WordBoundary':
                submaker.feed(chunk)
    srt_content = submaker.get_srt()
    with open('output/audio/scene1_clean_voice.srt', 'w', encoding='utf-8') as f_s: 
        f_s.write(srt_content)
    print('SRT Content:')
    print(srt_content)
    
    res = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 'output/audio/scene1_clean_voice.mp3'], capture_output=True, text=True)
    print('Duration:', res.stdout.strip())

if __name__ == '__main__':
    asyncio.run(main())
