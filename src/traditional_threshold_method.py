import os
import pandas as pd
import re 
import numpy as np
import matplotlib.pyplot as plt
import traceback
import shutil
import multiprocessing
from time import sleep
import time
def join_path(*path):
    return(os.path.join(*path))



def mkdir(f_folder,*folders):
    for f in [*folders]:
        mfolder = join_path(f_folder,f)
        if not os.path.exists(mfolder):
            os.makedirs(mfolder)

def get_testdata(time0,delt_time,data,candence):
    i = 0
    while True:
        testdata = data[(data["time"]>=time0+i*delt_time*3) & (data['time']<time0 + (i+1)*delt_time*3)]
        if testdata.shape[0]>= delt_time/candence-10 :
            return(testdata)
            break
        if time0+i*delt_time>data.time.max():
            return(pd.DataFrame(None))
            break
        i+=1

def fit(x,y,fit_order):
    fitdata = pd.DataFrame(None)
    fitdata['x'] = x
    fitdata['y'] = y
    mt = fitdata['x'].mean()
    fitdata['x'] = fitdata['x']-mt
    # fit_order=5
    for fitn in range(10):
        a=np.polyfit(fitdata['x'],fitdata['y'],fit_order)#用5次多项式拟合x，y数组
        b=np.poly1d(a)#拟合完之后用这个函数来生成多项式对象
        fitdata['yu'] = b(fitdata['x'])
        fitdata['rest'] = abs(fitdata['y'] - fitdata['yu'])
        rstd = fitdata['rest'].std()
        # print(fitdata)
        # plt.close()
        # plt.plot(fitdata['x'],fitdata['y'],'.')
        # plt.plot(x-mt,b(x-mt),)
        # plt.show()
        # plt.close()
        fitdata = fitdata[fitdata['rest'].abs()<rstd*4]
    fitdata['x'] = fitdata['x']+mt
    
    return(fitdata,a,b,rstd)

def get_fit_order(sepdata):
    if autorun == 'false':
        fit_order = re.search('fit_order *=.*[-+]?[0-9]*\.?[0-9]+',user_set).group().split('=')[-1].strip()
        fit_order = int(fit_order)
    if autorun == 'true':
        # everyoder = []
        # everyrest = []
        # selectorder = []
        # selectrest = []
        # for test_orderx in np.arange(5,41,5,):
        #     fitdata,a,b,rstd = fit(testdata['time'],testdata['light'],test_orderx)
        #     everyrest.append(rstd)
        #     everyoder.append(test_orderx)
    
        #     if not rstd > fit_tendency*rstd40:
        #         selectorder.append(test_orderx)
        #         selectrest.append(rstd)
        fitdata40,a40,b40,rstd40 = fit(sepdata['time'],sepdata['light'],40)
        for test_orderx in np.arange(3,41,3,):
            fitdata,a,b,rstd = fit(sepdata['time'],sepdata['light'],test_orderx)

            if not rstd > fit_tendency*rstd40:
                break
        fit_order = int(test_orderx)
        # plt.close()
        # plt.subplot(2,1,1)
        # plt.plot(everyoder,everyrest,)
        # plt.plot(selectorder,selectrest,'.')
        # plt.subplot(2,1,2)
        # plt.plot(testdata['time'],testdata['light'],'.')
        # plt.plot(fitdata['x'],fitdata['yu'])
        # plt.show()
        # plt.close()
    return(fit_order)



def get_fit_candence(data,candence):

    if autorun == 'false':
        delt_time = re.search('fit_time_scale *= *[-+]?[0-9]*\.?[0-9]+',user_set).group().split('=')[-1].strip()
        delt_time = float(delt_time)/3
        fit_order = re.search('fit_order *=.*[-+]?[0-9]*\.?[0-9]+',user_set).group().split('=')[-1].strip()
        fit_order = int(fit_order)
       
    if autorun == 'true':

        delt_timemin = candence*20
        num_grid = 30
        # fit_ordermax = 30
        # delt_time,fit_order = delt_timemin, fit_ordermax
        delt_time_grid = []
        for gridx in range(0,num_grid):
            delt_time_grid.append(delt_timemin*1.1**gridx)

        fit_order_grid = np.linspace(30,5,num_grid,endpoint=True)
        rest_grid = []
        # plt.plot(data.time,data.light,'.')
        # plt.show()
        for gridx in range(num_grid):
            test_rest = []
            for time0 in np.linspace(data.time.tolist()[0],data.time.tolist()[-1],20):
                testdata = get_testdata(time0,delt_time_grid[gridx],data,candence)

                if testdata.shape[0]<5:
                    continue
                testmt = testdata['time'].mean()
                testdata['time'] = testdata['time']-testmt
                testa=np.polyfit(testdata['time'],testdata['light'],int(fit_order_grid[gridx]))#用5次多项式拟合x，y数组
                testb=np.poly1d(testa)#拟合完之后用这个函数来生成多项式对象
                testdata['yu'] = testb(testdata['time'])
                testdata['rest'] = abs(testdata['light'] - testdata['yu'])
                rstd = testdata['rest'].std()
                test_rest.append(rstd)
            
            rest_grid.append(np.mean(sorted(test_rest)[:-3]))
        for selectgridx in np.linspace(0,num_grid-1,num_grid,endpoint=True):
            # print(selectgridx)
            selectgridx = int(selectgridx)
            if rest_grid[selectgridx]>candence_tendency*rest_grid[0] :
                break
        # print(rest_grid[selectgridx] > 6*rest_grid[0]/7+rest_grid[-1]/7 , rest_grid[selectgridx]>1.2*rest_grid[0])

        # selectgridx = 0
        delt_time = delt_time_grid[selectgridx]


        # plt.subplot(2,1,1)
        # plt.text(selectgridx,rest_grid[selectgridx],str(1.2)+str(rest_grid[selectgridx]>1.2*rest_grid[0]))
        # plt.plot(list(range(num_grid)),rest_grid)
        # plt.plot(selectgridx,rest_grid[selectgridx],'.',c = 'r')
        # plt.subplot(2,1,2)
        # plt.plot(data.time[:60],data.light[:60],'.')
        # plt.show()

        if delt_time>1.5:
            delt_time =1.5
    return(delt_time)
        

    


    # if autorun
def search_flare(light_file):
    start_time = time.perf_counter()
    filename = light_file.split(os.path.sep)[-1]
    data = pd.read_csv(light_file,header= None, names=['time','light','erro'])
    data = data.dropna(subset=['time','light'])
    
    cantimes = data.time[:100].tolist()
    candences = []
    for cantimex in range(99):
        candences.append(cantimes[cantimex+1]-cantimes[cantimex])
    selectcandences = sorted(candences)[10:20]
    candence = np.mean(selectcandences)

    delt_time = get_fit_candence(data,candence)

    # print(delt_time, fit_order)
    # 
    btime = data.time.min()
    etime = data.time.max()
    detrended = pd.DataFrame(None)
    ignoredata = []
    # print(btime,etime,111111111111111111)
    num_point = 0
    flareparameters={}
    for n in range(int((etime-btime)/delt_time+1)):
        sepdata = data[(data["time"]>=(delt_time*n-delt_time)+btime) & (data['time']<(delt_time*(n+1)+delt_time)+btime)]
        if sepdata.shape[0]>num_point:
            num_point = sepdata.shape[0]
        mt = sepdata['time'].mean()
        sepdata['x'] = sepdata['time']-mt
        sepdata['y'] = sepdata.light
        if len(sepdata['x'].tolist())<=45:
            continue        
        try:#判断是否可以成功拟合，无法拟合则跳过该文件
            np.polyfit(sepdata['x'],sepdata['y'], 5)
            np.polyfit(sepdata['x'],sepdata['y'], 40)
        except:
            print(traceback.format_exc())
            continue
        

        fit_order = get_fit_order(sepdata)
        # print(sepdata)
        # popt, pcov = curve_fit(fourier, x, y, [1.0] * 100,)
        # print(fitdata['x'],1111111111)
        fitdata,a,b,rstd = fit(sepdata['x'],sepdata['y'],fit_order)

        sepdata['fit_curve'] = b(sepdata['x'])
        sepdata['detrended_data'] = sepdata.y - sepdata.fit_curve

        flaredata = pd.DataFrame(None)
        flaredata['x'] = []
        flaredata['y'] = []
        step=5.25
        while flaredata.shape[0]==0 or flaredata.x.max()-flaredata.x.min() > (sepdata.x.max() - sepdata.x.min())/(5):
            flaredata = pd.DataFrame(None) 
            flaredata['x'] = []
            flaredata['y'] = []
            flaredata = sepdata[sepdata.detrended_data > rstd*step]

            if flaredata.shape[0]==0:
                break 
            if step> flare_threshold:

                break

            step+=0.1
        # picturemaxyindex = sepdata.y[sepdata.y == sepdata.y.max()].index[0]
        # timeofmaxy = sepdata.loc[picturemaxyindex,'time']
        # xinflaremaxy = round(timeofmaxy,5)
        if save_flare_picture == 'true' or save_all_picture == 'true':
            plt.plot(sepdata.time, sepdata.y, '.',label='original values',markersize=3)
            plt.plot(sepdata.time, sepdata.fit_curve, 'r',label='fit values',markersize=3)
            plt.title(filename)
        # plt.plot(flaredata.time, flaredata.y, 's',color='red',markersize=3)
        if flaredata.shape[0]>=3:


            columns = flaredata.columns.tolist()

            

            flaredata = np.array(flaredata)
            sepflaredata = [np.array([flaredata[0,:]])]
            sepfn=0
            for sepfnx in range(1,flaredata.shape[0]):
                if flaredata[sepfnx,columns.index('x')] - flaredata[sepfnx-1,columns.index('x')]>3.1*candence:
                    sepfn += 1
                    sepflaredata.append(np.array([flaredata[sepfnx,:]]))
                    continue
                sepflaredata[sepfn] = np.append(sepflaredata[sepfn],[flaredata[sepfnx,:]],axis=0) 
                


            
            for aflaredatax in sepflaredata:

                aflaredata = pd.DataFrame(aflaredatax,columns=columns)
                maxyindex = aflaredata.y.tolist().index(aflaredata.y.max())
                toppoint = (aflaredata.loc[maxyindex,'time'],aflaredata.y.max())
                pointduringflare = sepdata[(sepdata.time>=aflaredata.time.min())&(sepdata.time<=aflaredata.time.max())]

                if toppoint[0]>=(delt_time*n)+btime and toppoint[0]<(delt_time*(n+1))+btime and aflaredata.shape[0]>=3 and aflaredata.shape[0]/pointduringflare.shape[0]>=1-noise_rate:

                    
                    endjudge = True
                    fstarttime = None
                    fendtime = None
                    for xxx in sepdata.index:
                        if ((sepdata.detrended_data[xxx] > 0 and sepdata.detrended_data[xxx] < rstd*0.8) or (sepdata.detrended_data[xxx] < 0 and sepdata.detrended_data[xxx] < rstd*(-1.3))) and sepdata.time[xxx] < aflaredata.time.min():
                            fstarttime = sepdata.time[xxx]
                            fstartmag = sepdata.light[xxx]
                        if endjudge:
            
                            if ((sepdata.detrended_data[xxx] > 0 and sepdata.detrended_data[xxx] < rstd*0.8) or (sepdata.detrended_data[xxx] < 0 and sepdata.detrended_data[xxx] < rstd*(-1.3))) and sepdata.time[xxx] > aflaredata.time.max():
                                fendtime = sepdata.time[xxx]
                                fendmag = sepdata.light[xxx]
                                endjudge = False
                    if not fstarttime ==None and not fendtime == None:

                        personflaredata = sepdata[(sepdata.time>=fstarttime)&(sepdata.time<=fendtime)]
                        amplitude = personflaredata.detrended_data.max()
                        flaremaxyindex = personflaredata.y[personflaredata.y == personflaredata.y.max()].index[0]
                        flaretoppoint = (personflaredata.loc[flaremaxyindex,'time'],personflaredata.y.max())
                        flarename = str(round(fstarttime,5))+'~'+str(round(fendtime,5))
                        integrationflare = (personflaredata.time.max()-personflaredata.time.min())*personflaredata.detrended_data.mean()
                        falsepoint = personflaredata[(personflaredata.y>=fstartmag)&(personflaredata.y>=fendmag)]
                        if falsepoint.shape[0]/personflaredata.shape[0]>1-noise_rate:
                            flareparameters[flarename]=[filename,flaretoppoint[0],fstarttime,fendtime,amplitude,integrationflare,aflaredata,personflaredata]

                            plt.plot(personflaredata.time,personflaredata.light,'.',color='red')
                            plt.plot(aflaredata.time,aflaredata.light,'.',color='y')
                            plt.text(flaretoppoint[0],flaretoppoint[1],'Flare')
                            # plt.xlim(4*fstarttime-3*fendtime,4*fendtime-3*fstarttime)
                            if save_flare_picture == 'true' or save_all_picture == 'true':
                                plt.savefig(join_path(work_folder,'S_flare_pictures',filename+'_'+flarename+'.png'))
                            # plt.show()
                        if falsepoint.shape[0]/personflaredata.shape[0]<=1-noise_rate:
                            ignoredata.append([toppoint,aflaredata])
                            if save_flare_picture == 'true' or save_all_picture == 'true':
                                plt.plot(personflaredata.time,personflaredata.light,'.',color='red')
                                plt.plot(aflaredata.time,aflaredata.light,'.',color='y')
                                plt.text(flaretoppoint[0],flaretoppoint[1],'ignore')
                                plt.savefig(join_path(work_folder,'S_ignore_pictures',filename+'_'+flarename+'.png'))
                elif toppoint[0]>=(delt_time*n)+btime and toppoint[0]<(delt_time*(n+1))+btime and aflaredata.shape[0]>=3 and aflaredata.shape[0]/pointduringflare.shape[0]<1-noise_rate:
                    ignoredata.append([toppoint,aflaredata])
                    if save_flare_picture == 'true' or save_all_picture == 'true':
                        plt.plot(aflaredata.time,aflaredata.light,'.',color='y')
                        plt.text(toppoint[0],toppoint[1],'ignore')
                        plt.savefig(join_path(work_folder,'S_ignore_pictures',filename+'_'+str(n)+'.png'))
            
        if save_all_picture == 'true':
            plt.savefig(join_path(work_folder,'S_all_picture',filename+'_'+str(n)+'.png'))
        # plt.show()
        if save_flare_picture == 'true' or save_all_picture == 'true':
            plt.close()
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"[TIME] {filename} 用时: {elapsed:.3f} 秒")

    with open(join_path(work_folder,'runtime_log.csv'),'a') as rt:
        rt.write(f"{filename},{elapsed}\n")       
        sepdata = sepdata[(sepdata["time"]>=(delt_time*n)+btime) & (sepdata['time']<(delt_time*(n+1))+btime)]

        detrended = pd.concat([detrended, sepdata], ignore_index=True)
        # highpoint = highpoint.append(sepdata[sepdata.detrended_data > rstd*flare_threshold])

    print('n    order    delt_time              candence')
    print(num_point,'  ',fit_order,'  ',delt_time*3,candence*24*60,filename ,str(fi))
    # plt.subplot(2,1,2)

        # plt.text(ignorex[0][0],ignorex[0][1],'ignore')
    # plt.text(detrended.time[0],detrended.light.max(),str())
    wparameter = ''
    if len(flareparameters)>0:
        shutil.copyfile(light_file,join_path(work_folder,'S_flare_files',filename))
    for flarex in flareparameters:
        wparameter += flarex+','+str(flareparameters[flarex][:-2])[1:-1]+'\n'
    with open(join_path(work_folder,'Flare_pamareters.csv'),'a') as wflarefile:
        wflarefile.write(wparameter)
    # print(wparameter)
    if show_picture == 'true'or save_all_picture == 'true':
    
        plt.plot(detrended.time,detrended.light,'.')
        # plt.plot(highpoint.time,highpoint.light,'.','r')
        plt.plot(detrended.time,detrended.fit_curve)
        
    
        plt.title(filename)
        
        for flarex in flareparameters:
            plt.plot(flareparameters[flarex][-1].time,flareparameters[flarex][-1].light,'.',color = 'red')
            plt.plot(flareparameters[flarex][-2].time,flareparameters[flarex][-2].light,'.',color = 'y')
            plt.text(flareparameters[flarex][1],flareparameters[flarex][-1].y.max(),'Flare')
        for ignorex in ignoredata:
            plt.plot(ignorex[-1].time,ignorex[-1].light,'.',color='y')

        
        if save_all_picture == 'true':
            plt.savefig(join_path(work_folder,'S_all_picture',filename+'.png'))
        # plt.show()
        plt.close()








# script_path = os.getcwd()
script_path = os.path.dirname(__file__).replace('/','\\')
default_set = 'auto_run = true  #true or false\n\nprocess_num = 1        #线程数 \n\nlight_folder = none      # 光变曲线文件夹\n\nflare_threshold = 5.1     #越大越不容易识别为耀发越不容易误判\n\nnoise_rate = 0.35  #耀发处所允许的噪点比例\n\nsave_flare_picture = false     #true or false\n\nsave_all_picture = false     #true or false\n\nshow_picture = false     #true or false\n\nfit_tendency = 1.2       # 越小越倾向于采用更高级次多项式进行拟合拟合度越高 auto_run 为True 时有效\n\ncandence_tendency = 1.7       # 此值越小越倾向于采用更小的拟合宽度进行拟合拟合度越高 auto_run 为True 时有效\n\n\n\n\nfit_time_scale = 0.5     #拟合宽度auto_run 为 false时有效\n\nfit_order = 10         #所用多项式的次数auto_run 为 false时有效\n\n\n\n\n\n\n#如需恢复默认，删除此文件'





if not os.path.isfile(join_path(script_path, 'search.set')):
    with open(join_path(script_path, 'search.set'), 'w',encoding='UTF-8') as setfile:
        setfile.write(default_set)
with open(join_path(script_path, 'search.set'), encoding='UTF-8') as setfile:
    user_set = setfile.read()
# print(user_set)
light_folder = re.search('light_folder *=.*',user_set).group().split('#')[0].split('=')[-1].strip()
# print(light_folder)
assert not light_folder == 'none', 'please set path of light curves in file "'+join_path(script_path, 'search.set"')
assert os.path.exists(light_folder), 'wrong path of light curve folder'
work_folder = os.path.abspath(os.path.dirname(light_folder))
mkdir(work_folder,'S_all_picture','S_flare_pictures','S_flare_files','S_ignore_pictures')
if not os.path.isfile(join_path(work_folder,'Flare_pamareters.csv')):
    fscroe=open(join_path(work_folder,'Flare_pamareters.csv'),'w')
    fscroe.write('duration,files,peaktime,begin,end,amplitude,flare_integration\n')
    fscroe.close()
logpath = join_path(work_folder,'log')
if not os.path.isfile(join_path(work_folder,'runtime_log.csv')):
    with open(join_path(work_folder,'runtime_log.csv'),'w') as rt:
        rt.write("filename,seconds\n")
if os.path.exists(logpath):
    logf = open(logpath,'r')      
    try:
        log = logf.readlines()
    except:
        log = []
else:
    logf = open(logpath,'w')
    log = []
logf.close()

autorun = re.search('auto_run *= *(true|false)',user_set).group().split('=')[-1].strip()
n_core = re.search('process_num *= *[-+]?[0-9]*\.?[0-9]+',user_set).group().split('=')[-1].strip()
n_core = int(n_core)
flare_threshold = re.search('flare_threshold *= *[-+]?[0-9]*\.?[0-9]+',user_set).group().split('=')[-1].strip()
flare_threshold = float(flare_threshold)
fit_tendency = re.search('fit_tendency *= *[-+]?[0-9]*\.?[0-9]+',user_set).group().split('=')[-1].strip()
fit_tendency = float(fit_tendency)
candence_tendency = re.search('candence_tendency *= *[-+]?[0-9]*\.?[0-9]+',user_set).group().split('=')[-1].strip()
candence_tendency = float(candence_tendency)
noise_rate = re.search('noise_rate *= *[-+]?[0-9]*\.?[0-9]+',user_set).group().split('=')[-1].strip()
noise_rate = float(noise_rate)
save_flare_picture = re.search('save_flare_picture *= *(true|false)',user_set).group().split('=')[-1].strip()
save_all_picture = re.search('save_all_picture *= *(true|false)',user_set).group().split('=')[-1].strip()
show_picture = re.search('show_picture *= *(true|false)',user_set).group().split('=')[-1].strip()

total_start_time = time.perf_counter()
fi = -1

runs = {}
for light_file in os.listdir(light_folder):
    fi +=1
    if not light_file.endswith('.csv'):
        continue
    if light_file+'\n' in log:
        continue
    # if light_file != r'tess2022138205153-s0052-0000000008501064-0224-s_lc.fits.csv':
    #     continue
    # if fi<21:
    #     continue
    if len(runs) >=n_core:
        while True:#开启无限循环 检查开启的线程数
            sleep(1)#每隔0.1秒检查一次
            runingfiles = list(runs.keys())
            for runingfile in runingfiles:#执行一次检查，检查每一个线程
                
                if not runs[runingfile].is_alive():#如果线程线程已经运行结束
                    logf = open(logpath,'a')
                    logf.write(runingfile+'\n')
                    logf.close()

                    del runs[runingfile] #从线程列表里面删除线程


                    
            if len(runs)<n_core:#执行一次线程检查之后，查看线程数是不是减少了，如果减少了打破无限循环的while检查
                break
            
    if len(runs)<n_core:
        if __name__ == '__main__':
            Threadt =multiprocessing.Process(target=search_flare, args=(join_path(light_folder,light_file),))#创建一个线程
            runs[light_file] = Threadt#把线程放到run列表
            Threadt.start()#运行线程

runingfiles = list(runs.keys())
for runingfile in runingfiles:#执行一次检查，检查每一个线程
    
    runs[runingfile].join()#如果线程线程已经运行结束
    
    logf = open(logpath,'a')
    logf.write(runingfile+'\n')
    logf.close()

total_end_time = time.perf_counter()
total_elapsed = total_end_time - total_start_time
print(f"\n==============================")
print(f"总耗时: {total_elapsed:.3f} 秒")
print(f"平均每条耗时: {total_elapsed/(fi+1):.3f} 秒")
print(f"==============================")

with open(join_path(work_folder,'runtime_summary.txt'),'w') as rt:
    rt.write(f"Total runtime: {total_elapsed:.3f} seconds\n")
    rt.write(f"Average per file: {total_elapsed/(fi+1):.3f} seconds\n")