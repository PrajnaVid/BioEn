from __future__ import print_function
import os
import sys
import numpy as np
from bioen import optimize
from bioen import fileio as fio
import pickle

# relative tolerance for value comparison
#tol = 1.e-14
tol = 5.e-14
tol_min = 1.e-1

verbose = False
create_reference_values = False

myfio=True
#myfio=False

filenames = [
    "./data/data_potra_part_2_logw_M205xN10.pkl",  # realistic test case provided by Katrin, has small theta
#    "./data/data_16x15.pkl",                       # synthetic test case
#    "./data/data_deer_test_logw_M808xN10.pkl",
#    "./data/data_potra_part_2_logw_M205xN10.pkl",
#    #    "./data/data_potra_part_1_logw_M808xN80.pkl",   ## (*)(1)
#    #    "./data/data_potra_part_2_logw_M808xN10.pkl"  # ## (*)(2) with default values (tol,step_size) gsl/conj_pr gives NaN
]


# (*) require specific tunning of parameters.
# (*)(1) scipy_py/cg and scipy_c/cg
# (*)(2) GSL/conjugate_pr and GSL/bfgs


def available_tests():

    exp = {}

    if (create_reference_values):
        exp['GSL'] = { 'bfgs' : {} }
        return exp

    #exp['scipy_py'] = { 'bfgs':{}, 'lbfgs':{} ,'cg':{} }
    exp['scipy_py'] = { 'bfgs':{}, 'lbfgs':{}  }
    exp['scipy_c']  = { 'bfgs':{}, 'lbfgs':{} ,'cg':{} }

    if (optimize.util.library_gsl()):
        exp['GSL'] = { 'conjugate_fr':{}, 'conjugate_pr':{}, 'bfgs2':{}, 'bfgs':{}, 'steepest_descent':{} }

    if (optimize.util.library_lbfgs()):
        exp['LBFGS'] = { 'lbfgs':{} }

    return exp



def run_test_optimum_logw(file_name=filenames[0], library='scipy/py', caching=False):
    print("=" * 80)

    if (create_reference_values):
        os.environ["OMP_NUM_THREADS"] = "1"

    if "OMP_NUM_THREADS" in os.environ:
        print("OPENMP NUM. THREADS = ", os.environ["OMP_NUM_THREADS"])

    exp = available_tests()

    # Run the optimizer for all the available tests
    for minimizer in exp:
        for algorithm in exp[minimizer]:


            ### compare
            #with open(file_name, 'r') as ifile:
            #    [pGInit, pG, py, pyTilde, pYTilde, pw0, ptheta] = pickle.load(ifile)

            #new_mydict = fio.load_dict(file_name)
            #[hGInit, hG, hy, hyTilde, hYTilde, hw0, htheta] = fio.get_list_from_dict(new_mydict,"GInit", "G", "y", "yTilde", "YTilde", "w0", "theta")

            #print ("COMPARISON OF PICKLE AND H5PY") 

            #eval_diff = optimize.util.compute_relative_difference_for_values(ptheta, htheta)
            #print ("Theta diff ", eval_diff) 

            #print("p type " , str(type(py)))
            #print("p shape " , py.shape)
            #print("h type " , str(type(hy)))
            #print("h shape " , hy.shape)
            #print (py)
            #print (hy)
            #dg, idx = optimize.util.compute_relative_difference_for_arrays(py, hy)
            #print("relative difference of gradient = y {} (maximum at index {})".format(dg, idx))

            #dg, idx = optimize.util.compute_relative_difference_for_arrays(pyTilde, hyTilde)
            #print("relative difference of gradient = yTilde {} (maximum at index {})".format(dg, idx))
            #dg, idx = optimize.util.compute_relative_difference_for_arrays(pYTilde, hYTilde)
            #print("relative difference of gradient = YTilde {} (maximum at index {})".format(dg, idx))
            #dg, idx = optimize.util.compute_relative_difference_for_arrays(pw0, hw0)
            #print("relative difference of gradient = w0 {} (maximum at index {})".format(dg, idx))
            

            if not myfio :
                with open(file_name, 'r') as ifile:
                    [GInit, G, y, yTilde, YTilde, w0, theta] = pickle.load(ifile)
            else:
                new_mydict = fio.load_dict(file_name)
                [GInit, G, y, yTilde, YTilde, w0, theta] = fio.get_list_from_dict(new_mydict,"GInit", "G", "y", "yTilde", "YTilde", "w0", "theta")




            minimizer_tag = minimizer
            use_c_functions = True
            if (minimizer == 'scipy_py'):
                minimizer_tag = 'scipy'
                use_c_functions = False

            if (minimizer == 'scipy_c'):
                minimizer_tag = 'scipy'

            # get default parameter's configuration for a minimizer
            params = optimize.minimize.Parameters(minimizer_tag)

            params['cache_ytilde_transposed'] = caching
            params['use_c_functions'] = use_c_functions
            params['algorithm'] = algorithm
            params['verbose'] = verbose

            if verbose:
                print("-" * 80)
                print(params)

            # run optimization
            wopt, yopt, gopt, fmin_ini, fmin_fin =  \
                optimize.log_weights.find_optimum(GInit, G, y, yTilde, YTilde, theta, params)

            # store the results in the structure
            exp[minimizer][algorithm]['wopt'] = wopt
            exp[minimizer][algorithm]['yopt'] = yopt
            exp[minimizer][algorithm]['gopt'] = gopt
            exp[minimizer][algorithm]['fmin_ini'] = fmin_ini
            exp[minimizer][algorithm]['fmin_fin'] = fmin_fin


    print ("XXXXXXXXXXX DONE WITH OPTIMIZATIONS XXXXXXXXXXXXXXXX")

    if (create_reference_values):
        print("-" * 80)

        for minimizer in exp:
            for algorithm in exp[minimizer]:
                fmin_fin = exp[minimizer][algorithm]['fmin_fin']

                print(" === CREATING REFERENCE VALUES ===")
                ref_file_name = os.path.splitext(file_name)[0] + ".ref"
                with open(ref_file_name, "wb") as f:
                    pickle.dump(fmin_fin, f)
                    #fio.dump(fmin_fin, f)
                print(" [%8s][%4s] -- fmin: %.16f --> %s" % (minimizer, algorithm, fmin_fin, ref_file_name))
                print("=" * 34, " END TEST ", "=" * 34)
                print("%" * 80)
    else:

        # get reference value
        ref_file_name = os.path.splitext(file_name)[0] + ".ref"
        available_reference = False
        if (os.path.isfile(ref_file_name)):
            available_reference = True
            with open(ref_file_name, "rb") as f:
                fmin_reference = pickle.load(f)

        # print results
        print("=" * 80)
        print(" [LOGW] CHECK RESULTS for file [ %s ] -- caching(%s)" % (file_name, caching))

        if (available_reference):
            print("-" * 80)
            print(" === REFERENCE EVALUATION ===")

            for minimizer in exp:
                for algorithm in exp[minimizer]:
                    fmin_fin = exp[minimizer][algorithm]['fmin_fin']

                    eval_diff = optimize.util.compute_relative_difference_for_values(fmin_fin, fmin_reference)
                    print(" [%8s][%16s] -- fmin: %.16f -- fmin_reference   : %.16f  -- diff(tol=%1.0e) = %.16f" % (
                        minimizer, algorithm, fmin_fin, fmin_reference, tol_min, eval_diff))


            for minimizer in exp:
                for algorithm in exp[minimizer]:
                    fmin_fin = exp[minimizer][algorithm]['fmin_fin']
                    eval_diff = optimize.util.compute_relative_difference_for_values(fmin_fin, fmin_reference)
                    assert(np.all(eval_diff < tol_min))

        else:
            print("-" * 80)
            print(" === REFERENCE EVALUATION === ")
            print(" [Reference not found]  To re-generate reference values enable create_reference_values=True and relaunch")
            assert(False)

        print("-" * 80)
        print(" === RETURNED GRADIENT EVALUATION ===")

        # re-evaluation of minimum for the returned vector
    
        if not myfio :
            with open(file_name, 'r') as ifile:
                [GInit, G, y, yTilde, YTilde, w0, theta] = pickle.load(ifile)
        else:
            new_mydict = fio.load_dict(file_name)
            [GInit, G, y, yTilde, YTilde, w0, theta] = fio.get_list_from_dict(new_mydict,"GInit", "G", "y", "yTilde", "YTilde", "w0", "theta")




        for minimizer in exp:
            for algorithm in exp[minimizer]:
                gopt = exp[minimizer][algorithm]['gopt']
                exp[minimizer][algorithm]['re_fmin'] = \
                    optimize.log_weights.bioen_log_posterior(gopt, GInit, G, yTilde, YTilde, theta, use_c=True)


        # print differences
        for minimizer in exp:
            for algorithm in exp[minimizer]:
                re_fmin = exp[minimizer][algorithm]['re_fmin']
                fmin_fin = exp[minimizer][algorithm]['fmin_fin']
                eval_diff = optimize.util.compute_relative_difference_for_values(fmin_fin, re_fmin)
                print(" [%8s][%16s] -- fmin: %.16f -- fmin_for_gradient: %.16f  -- diff(tol=%1.0e) = %.16f" % (
                    minimizer, algorithm, fmin_fin, re_fmin, tol, eval_diff))

        print("=" * 34, " END TEST ", "=" * 34)
        print("%" * 80)

        # validate differences
        for minimizer in exp:
            for algorithm in exp[minimizer]:
                re_fmin = exp[minimizer][algorithm]['re_fmin']
                fmin_fin = exp[minimizer][algorithm]['fmin_fin']

                eval_diff = optimize.util.compute_relative_difference_for_values(fmin_fin, re_fmin)
                assert(np.all(eval_diff < tol))
    return




def test_find_opt_analytical_grad():
    """Entry point for py.test."""
    print("")
    optimize.minimize.set_fast_openmp_flag(0)
    for file_name in filenames:
        caching_options = ["False"]
        #if (not create_reference_values):
        #    caching_options = ["False", "True"]

        for caching in caching_options:
            run_test_optimum_logw(file_name=file_name, caching=caching)

