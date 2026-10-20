#!/usr/bin/env python3
"""A070-v0.2.3 observational evidence only: no physical wave-speed claim.
Frames are indexed in the slowed video. Recorded frame time = frame_index/240,
provided all original 240-fps frames survived 1:1. Not calibrated to absolute SST t.
"""
import argparse, csv, hashlib, json, math
from pathlib import Path
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

CONTRACT = dict(version='A070-video-plan-v0.2.3', video_fps_nominal=240.0,
                interval_playback_s=[8.0,19.0], axis_roi_px=[422,498],
                control_left_px=[335,395], control_right_px=[526,586],
                vertical_roi_px=[460,1370], vertical_step_px=3,
                note='Contrast proxy only. No unique wavefront velocity inferred.')

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda: f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def video_facts(path):
    v=cv2.VideoCapture(str(path));
    if not v.isOpened(): raise RuntimeError(f'Cannot read {path}')
    facts=dict(frame_count=int(v.get(cv2.CAP_PROP_FRAME_COUNT)),
               stored_fps=float(v.get(cv2.CAP_PROP_FPS)),
               width=int(v.get(cv2.CAP_PROP_FRAME_WIDTH)),
               height=int(v.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    v.release()
    facts['duration_playback_s']=facts['frame_count']/facts['stored_fps']
    facts['duration_recording_if_1to1_s']=facts['frame_count']/CONTRACT['video_fps_nominal']
    facts['playback_slowdown_if_1to1']=CONTRACT['video_fps_nominal']/facts['stored_fps']
    facts['user_revolution_playback_s_approx']=14.0
    facts['estimated_rotation_rpm']=60.0*facts['playback_slowdown_if_1to1']/14.0
    facts['example_event_playback_s']=12
    facts['example_event_recorded_s']=12/facts['playback_slowdown_if_1to1']
    return facts

def get_frame(v, t, fps):
    v.set(cv2.CAP_PROP_POS_FRAMES,round(t*fps))
    ok,fr=v.read()
    if not ok:raise RuntimeError(f'Cannot read frame {t}')
    return cv2.cvtColor(fr,cv2.COLOR_BGR2RGB)

def montage(video,out,fps):
    ts=[10.5,11,11.5,12,12.5,13,13.5,14]
    v=cv2.VideoCapture(str(video))
    sheet=Image.new('RGB',(320*4,450*2),'white');d=ImageDraw.Draw(sheet)
    for i,t in enumerate(ts):
        fr=get_frame(v,t,fps)
        im=Image.fromarray(fr[550:1500,300:650]).resize((315,430))
        x=(i%4)*320;y=(i//4)*450
        sheet.paste(im,(x,y+20));d.text((x+5,y+2),f'{t:4.1f} s playback',fill='black')
    v.release();sheet.save(out,quality=92)

def kymograph(video,outpng,outnpz,fps):
    v=cv2.VideoCapture(str(video));t0,t1=CONTRACT['interval_playback_s']
    v.set(cv2.CAP_PROP_POS_FRAMES,round(t0*fps))
    series=[];times=[]
    lo,hi=CONTRACT['vertical_roi_px'];dy=CONTRACT['vertical_step_px']
    for fi in range(round(t0*fps),round(t1*fps)+1):
        ok,frame=v.read()
        if not ok:break
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY).astype(np.float32)
        a,b=CONTRACT['axis_roi_px'];la,lb=CONTRACT['control_left_px'];ra,rb=CONTRACT['control_right_px']
        central=gray[lo:hi:dy,a:b]
        flanks=np.concatenate([gray[lo:hi:dy,la:lb],gray[lo:hi:dy,ra:rb]],axis=1)
        series.append(np.quantile(central,.82,axis=1)-np.quantile(flanks,.82,axis=1))
        times.append(fi/fps)
    v.release()
    M=np.array(series,dtype=np.float32).T
    times=np.array(times);ys=np.arange(lo,hi,dy)
    smooth=gaussian_filter(M,(2,.8))
    band=smooth-gaussian_filter(smooth,(2,16))
    np.savez_compressed(outnpz,playback_s=times,recording_s=times*fps/240,
                        y_image_px=ys,relative_contrast=M,dynamic_contrast=band)
    fig,axs=plt.subplots(2,1,figsize=(11,7.5),layout='constrained')
    for ax,arr,title in [(axs[0],M,'Central image contrast minus flanks'),
                         (axs[1],band,'Time-high-pass contrast (visual aid only)')]:
        lim=np.quantile(np.abs(arr),.993)
        ax.imshow(arr,aspect='auto',extent=[times[0],times[-1],hi,lo],origin='upper',
                  cmap='coolwarm',vmin=-lim,vmax=lim)
        ax.axvline(12,ls='--',color='black',lw=1)
        ax.set(ylabel='Video y (pixels, downward)',title=title)
    axs[-1].set_xlabel('Playback time [s], ~8x slowed')
    fig.savefig(outpng,dpi=170);plt.close(fig)
    return {'samples_t':len(times),'samples_y':len(ys),'front_speed':'UNRESOLVED',
            'cause':'No uniquely identified propagating phasefront; bubbles/refraction/surface change confound.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--video',required=True)
    ap.add_argument('--output',default='results');args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    video=Path(args.video);facts=video_facts(video)
    facts['input_sha256']=sha256_file(video)
    summary=kymograph(video,out/'axial_kymograph.png',out/'axial_contrast.npz',facts['stored_fps'])
    montage(video,out/'central_frames.jpg',facts['stored_fps'])
    with open(out/'video_audit.json','w',encoding='utf-8') as f:
        json.dump({'contract':CONTRACT,'metadata':facts,'analysis':summary},f,indent=2)
    print(json.dumps({'fps':facts['stored_fps'],'duration_s':facts['duration_recording_if_1to1_s'],
                      'wave_speed':summary['front_speed']},indent=2))
if __name__=='__main__':main()
