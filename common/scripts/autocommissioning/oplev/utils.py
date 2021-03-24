import foton

# print(foton.__file__)
# #print(dir(foton))
# fname = '/opt/rtcds/kamioka/k1/chans/K1VISIMMT1.txt'
# immt1 = foton.FilterFile(fname)
# print(dir(immt1['IMMT1_TM_OLDCCTRL_P']))
# filt0 = immt1['IMMT1_TM_OLDCCTRL_P'][0]
# print(dir(filt0))
# hoge = filt0.design
# print(hoge)
# filt4 = immt1['IMMT1_TM_OLDCCTRL_P'][4]
# print(filt4.name)
# filt4._set_design('')
# filt4.name = ''
# #filt4.design
# immt1.write()


if __name__=='__main__':
    dofs = ['L','T']
    optics = ['ETMXT','ETMYT','ITMXT','ITMYT','BST','SR2T','SR3T','SRMT',
              'ETMXP','ETMYP','ITMXP','ITMYP','BSP','SR2P','SR3P','SRMP',
              'PRM','PR2','PR3',
              'MCE','MCI','MCO','IMMT1','IMMT2','OMMT1','OMMT2','OSTM']
    #optics = ['PRM','PR2','PR3']
    #optics = ['ETMXMON']
    optics = ['PR2']
    ftname_susmod = ['susmod','SusMod','Susmod','susMod','SUSMOD',
                     'susmodel','SusModel','Susmodel','susModel','SUSMODEL',
                     'model','Model']
    ftname_minus = ['-1']
    with open('huge.txt','w') as f:
        for optic in optics:
            fname = '/opt/rtcds/kamioka/k1/chans/K1VIS{0}.txt'.format(optic)
            #fname = '../../../k1/fotonfiles/K1VIS{0}.txt'.format(optic)
            ff = foton.FilterFile(fname)        
            for dof in dofs:
                #fbname = '{0}_BF_SC_{1}'.format(optic,dof)
                for key,val in ff.items():
                    fbname = key
                    for i in range(10):
                        ftname = val[i].name
                        ftdesign = val[i].design
                        if ftname in ftname_minus:
                            #if i != 9:
                            print(fbname,i,val[9].name)
                            txt = '{0} {1}\n'.format(fbname,i)
                            f.write(txt)                                
                            #print(i,'- '+ftname+' '+ftdesign)
                    #filt0 = ff[fbname][i]
                    #hoge = filt0.design
                    #txt = '{0} {1} {2}\n'.format(fbname,i,hoge)
                    #f.write(txt)
    
