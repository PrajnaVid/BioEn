from __future__ import print_function
import os
import sys
import numpy as np
from bioen import fileio as fio
from bioen import optimize
import pickle


# relative tolerance for value comparison
tol = 5.e-14
tol_min = 1.e-1

verbose = False
create_reference_values = False


filenames = [
    "./data/data_deer_test_forces_M808xN10.pkl",
#    "./data/data_forces_M64xN64.pkl"
]


def available_tests():

    exp = {}

    if (create_reference_values):
        exp['GSL'] = { 'bfgs' : {} }
        return exp

    exp['scipy_py'] = { 'bfgs':{}, 'lbfgs':{} ,'cg':{} }
    exp['scipy_c']  = { 'bfgs':{}, 'lbfgs':{} ,'cg':{} }

    if (optimize.util.library_gsl()):
        exp['GSL'] = { 'conjugate_fr':{}, 'conjugate_pr':{}, 'bfgs2':{}, 'bfgs':{}, 'steepest_descent':{} }

    if (optimize.util.library_lbfgs()):
        exp['LBFGS'] = { 'lbfgs':{} }

    return exp


def run_test_optimum_forces(file_name=filenames[0], caching=False):

    print("=" * 80)

    if (create_reference_values):
        os.environ["OMP_NUM_THREADS"] = "1"

    if "OMP_NUM_THREADS" in os.environ:
        print(" OPENMP NUM. THREADS = ", os.environ["OMP_NUM_THREADS"])

    exp = available_tests()

    for minimizer in exp:
        for algorithm in exp[minimizer]:

            #with open(file_name, 'rb') as ifile:
            #    [forces_init, w0, y, yTilde, YTilde, theta] = pickle.load(ifile)

            new_mydict = fio.load_dict(file_name)
            [forces_init, w0, y, yTilde, YTilde, theta] = fio.get_list_from_dict(new_mydict,"forces_init", "w0", "y", "yTilde", "YTilde", "theta")



            minimizer_tag = minimizer
            use_c_functions = True
            if (minimizer == 'scipy_py'):
                minimizer_tag = 'scipy'
                use_c_functions = False

            if (minimizer == 'scipy_c'):
                minimizer_tag = 'scipy'


            params = optimize.minimize.Parameters(minimizer_tag)
            params['cache_ytilde_transposed'] = caching
            params['use_c_functions'] = use_c_functions
            params['algorithm'] = algorithm
            params['verbose'] = verbose

            if verbose:
                print("-" * 80)
                print("", params)

            # run optimization
            wopt, yopt, forces, fmin_ini, fmin_fin, chiSqr, S = \
                optimize.forces.find_optimum(forces_init, w0, y, yTilde, YTilde, theta, params)


            # store the results in the structure
            exp[minimizer][algorithm]['wopt'] = wopt
            exp[minimizer][algorithm]['yopt'] = yopt
            exp[minimizer][algorithm]['forces'] = forces
            exp[minimizer][algorithm]['fmin_ini'] = fmin_ini
            exp[minimizer][algorithm]['fmin_fin'] = fmin_fin
            exp[minimizer][algorithm]['chiSqr'] = chiSqr
            exp[minimizer][algorithm]['S'] = S


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
        print("-" * 80)
        print(" [FORCES] CHECK RESULTS for file [ %s ] -- caching(%s)" % (file_name, caching))

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
        # re-evaluation of minimum for the the returned vector


        #with open(file_name, 'r') as ifile:
        #    [forces_init, w0, y, yTilde, YTilde, theta] = pickle.load(ifile)

        new_mydict = fio.load_dict(file_name)
        [forces_init, w0, y, yTilde, YTilde, theta] = fio.get_list_from_dict(new_mydict,"forces_init", "w0", "y", "yTilde", "YTilde", "theta")



        for minimizer in exp:
            for algorithm in exp[minimizer]:

                forces = exp[minimizer][algorithm]['forces']
                exp[minimizer][algorithm]['re_fmin'] = \
                    optimize.forces.bioen_log_posterior(forces, w0, y, yTilde, YTilde, theta, use_c=True)

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


def test_find_opt_analytical_grad_forces():
    """Entry point for py.test."""
    print("")
    optimize.minimize.set_fast_openmp_flag(0)
    for file_name in filenames:

        caching_options = ["False"]
        if (not create_reference_values):
            caching_options = ["False", "True"]

        for caching in caching_options:
            run_test_optimum_forces(file_name=file_name, caching=caching)
