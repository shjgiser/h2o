import unittest, time, sys, random, math, getpass
sys.path.extend(['.','..','py'])
import h2o, h2o_cmd, h2o_hosts, h2o_import as h2i, h2o_util, h2o_browse as h2b

DO_TRY_SCIPY = False

def twoDecimals(l): 
    if isinstance(l, list):
        return ["%.2f" % v for v in l] 
    else:
        return "%.2f" % l

# have to match the csv file?
# dtype=['string', 'float');
def generate_scipy_comparison(csvPathname, dtype):
    # this is some hack code for reading the csv and doing some percentile stuff in scipy
    # from numpy import loadtxt, genfromtxt, savetxt
    import numpy as np
    import scipy as sp

    dataset = np.genfromtxt(
        open(csvPathname, 'r'),
        delimiter=',',
        skip_header=1,
        dtype=None); # guess!

    print "csv read for training, done"
    # we're going to strip just the last column for percentile work
    # used below
    NUMCLASSES = 10
    print "csv read for training, done"

    # data is last column
    # drop the output
    print dataset.shape
    target = [x[1] for x in dataset]
    # we may have read it in as a string. coerce to number
    targetFP = np.array(target, np.float)

    if 1==0:
        n_features = len(dataset[0]) - 1;
        print "n_features:", n_features

        # get the end
        # target = [x[-1] for x in dataset]
        # get the 2nd col

        print "histogram of target"
        print target
        print sp.histogram(target, bins=NUMCLASSES)

        print target[0]
        print target[1]

    thresholds   = [0.01, 0.05, 0.1, 0.25, 0.33, 0.5, 0.66, 0.75, 0.9, 0.95, 0.99]
    # per = [100 * t for t in thresholds]
    per = [1 * t for t in thresholds]
    print "sp per:", per
    from scipy import stats
    # a = stats.scoreatpercentile(target, per=per)
    a = stats.mstats.mquantiles(targetFP, prob=per)
    print "sp percentiles:", a

class Basic(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global SEED, localhost
        SEED = h2o.setup_random_seed()
        localhost = h2o.decide_if_localhost()
        h2o.beta_features = True # to get the browser page special tab
        if (localhost):
            h2o.build_cloud(node_count=1, base_port=54327)
        else:
            h2o_hosts.build_cloud_with_hosts(node_count=1)
        h2o.beta_features = False
        # h2b.browseTheCloud()

    @classmethod
    def tearDownClass(cls):
        # h2o.sleep(3600)
        h2o.tear_down_cloud()

    def test_summary2_unifiles(self):
        SYNDATASETS_DIR = h2o.make_syn_dir()

        # old with 20 bins
        tryList = [
            # colname, (min, 25th, 50th, 75th, max)
            ('runif.csv', 'x.hex', [
                ('' ,  1.00, 5000.0, 10000.0, 15000.0, 20000.00),
                ('D', -5000.00, -3750.0, -2445, -1200.0, 99),
                ('E', -100000.0, -50000.0, 1613.0, 50000.0, 100000.0),
                ('F', -1.00, -0.48, 0.0087, 0.50, 1.00),
            ], ['string', 'float', 'float', 'float'],
            ),

            ('runifA.csv', 'A.hex', [
                ('',  1.00, 26.00, 51.00, 76.00, 100.0),
                ('x', -99.0, -43.0, 6.90, 58.00, 91.7),
            ], ['string', 'float'],
            ),

            ('runifB.csv', 'B.hex', [
                ('',  1.00, 2501.00, 5001.00, 7501.00, 10000.00),
                ('x', -100.00, -50.0, 0.85, 51.7, 100,00),
            ], ['string', 'float'],
            ),

            ('runifC.csv', 'C.hex', [
                ('',  1.00, 25002.00, 50002.00, 75002.00, 100000.00),
                ('x', -100.00, -50.45, -1.18, 49.28, 100.00),
            ], ['string', 'float'],
            ),

        ]
        # new with 1000 bins. copy expected from R
        tryList = [
            # colname, (min, 25th, 50th, 75th, max)
            ('runif.csv', 'x.hex', [
                ('' ,  1.00, 5000.0, 10000.0, 15000.0, 20000.00),
                ('D', -5000.00, -3735.0, -2443, -1187.0, 99.8),
                ('E', -100000.0, -49208.0, 1783.8, 50621.9, 100000.0),
                ('F', -1.00, -0.4886, 0.00868, 0.5048, 1.00),
            ], ['string', 'float', 'float', 'float'],
            ),

            ('runifA.csv', 'A.hex', [
                ('',  1.00, 26.00, 51.00, 76.00, 100.0),
                ('x', -99.0, -44.7, 7.80, 58.00, 91.7),
            ], ['string', 'float'],
            ),

            ('runifB.csv', 'B.hex', [
                ('',  1.00, 2501.00, 5001.00, 7501.00, 10000.00),
                ('x', -100.00, -50.0, 0.987, 51.7, 100,00),
            ], ['string', 'float'],
            ),

            ('runifC.csv', 'C.hex', [
                ('',  1.00, 25002.00, 50002.00, 75002.00, 100000.00),
                ('x', -100.00, -50.45, -1.135, 49.28, 100.00),
            ], ['string', 'float'],
            ),

        ]


        timeoutSecs = 10
        trial = 1
        n = h2o.nodes[0]
        lenNodes = len(h2o.nodes)

        x = 0
        timeoutSecs = 60
        for (csvFilename, hex_key, expectedCols, dtype) in tryList:
            h2o.beta_features = False

            csvPathname = csvFilename
            parseResult = h2i.import_parse(bucket='smalldata', path=csvPathname, 
                schema='put', hex_key=hex_key, timeoutSecs=10, doSummary=False)

            print csvFilename, 'parse time:', parseResult['response']['time']
            print "Parse result['destination_key']:", parseResult['destination_key']

            # We should be able to see the parse result?
            inspect = h2o_cmd.runInspect(None, parseResult['destination_key'])
            print "\n" + csvFilename

            numRows = inspect["num_rows"]
            numCols = inspect["num_cols"]

            h2o.beta_features = True
            summaryResult = h2o_cmd.runSummary(key=hex_key)
            h2o.verboseprint("summaryResult:", h2o.dump_json(summaryResult))

            summaries = summaryResult['summaries']
            for expected, column in zip(expectedCols, summaries):

                # ('',  '1.00', '25002.00', '50002.00', '75002.00', '100000.00'),
                colname = column['colname']
                self.assertEqual(colname, expected[0])

                coltype = column['type']
                nacnt = column['nacnt']

                stats = column['stats']
                stattype= stats['type']

                # FIX! we should compare mean and sd to expected?
                mean = stats['mean']
                sd = stats['sd']

                print "colname:", colname, "mean (2 places): %s", twoDecimals(mean)
                print "colname:", colname, "std dev. (2 places): %s", twoDecimals(sd)

                zeros = stats['zeros']

                mins = stats['mins']

                # estimate of error bounds
                maxDelta = ((expected[5] - expected[1])/20.0) / 2.0
                maxDelta = 1.05 * maxDelta
                # should be tighter now?
                maxDelta = 0.5 * maxDelta
                h2o_util.assertApproxEqual(mins[0], expected[1], rel=0.008, msg='min is not approx. expected')

                maxs = stats['maxs']
                h2o_util.assertApproxEqual(maxs[0], expected[5], rel=0.008, msg='max is not approx. expected')

                pct = stats['pct']
                # the thresholds h2o used, should match what we expected
                expectedPct= [0.01, 0.05, 0.1, 0.25, 0.33, 0.5, 0.66, 0.75, 0.9, 0.95, 0.99]

                pctile = stats['pctile']
                h2o_util.assertApproxEqual(pctile[3], expected[2], rel=maxDelta, msg='25th percentile is not approx. expected')
                h2o_util.assertApproxEqual(pctile[5], expected[3], rel=maxDelta, msg='50th percentile (median) is not approx. expected')
                h2o_util.assertApproxEqual(pctile[7], expected[4], rel=maxDelta, msg='75th percentile is not approx. expected')

                hstart = column['hstart']
                hstep = column['hstep']
                hbrk = column['hbrk']
                hcnt = column['hcnt']

                print "pct:", pct
                print ""

                for b in hcnt:
                    # should we be able to check for a uniform distribution in the files?
                    e = .1 * numRows
                    # self.assertAlmostEqual(b, .1 * rowCount, delta=.01*rowCount, 
                    #     msg="Bins not right. b: %s e: %s" % (b, e))

    
                pt = twoDecimals(pctile)
                mx = twoDecimals(maxs)
                mn = twoDecimals(mins)
                print "colname:", colname, "pctile (2 places):", pt
                print "colname:", colname, "maxs: (2 places):", mx
                print "colname:", colname, "mins: (2 places):", mn

                # FIX! we should do an exec and compare using the exec quantile too
                compareActual = mn[0], pt[3], pt[5], pt[7], mx[0]
                print "min/25/50/75/max colname:", colname, "(2 places):", compareActual
                print "maxs colname:", colname, "(2 places):", mx
                print "mins colname:", colname, "(2 places):", mn

            trial += 1

            if DO_TRY_SCIPY:
                csvPathname1 = h2i.find_folder_and_filename('smalldata', csvPathname, returnFullPath=True)
                generate_scipy_comparison(csvPathname1, dtype=dtype)

if __name__ == '__main__':
    h2o.unit_main()
