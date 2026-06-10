import java.io.IOException;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

/**
 * 4 jobs MapReduce pour l'analyse d'un dataset e-commerce.
 *
 * Format CSV attendu (1 ligne = 1 commande) :
 *   order_id, customer_id, product_id, category,
 *   seller_region, customer_region, price, freight_value,
 *   review_score, order_date (YYYY-MM)
 *
 * Usage :
 *   hadoop jar ecommerce.jar EcommerceAnalysis <job> <input> <output>
 *   job = revenue_category | orders_region | ratings | monthly_trend
 */
public class EcommerceAnalysis {

    // indices des colonnes dans le CSV
    private static final int COL_CATEGORY     = 3;
    private static final int COL_CUST_REGION  = 5;
    private static final int COL_PRICE        = 6;
    private static final int COL_SCORE        = 8;
    private static final int COL_DATE         = 9;

    // ----------------------------------------------------------------
    // JOB 1 — Chiffre d'affaires par catégorie
    // ----------------------------------------------------------------

    public static class RevenueByCategoryMapper
            extends Mapper<Object, Text, Text, DoubleWritable> {

        private final Text          category = new Text();
        private final DoubleWritable price    = new DoubleWritable();

        @Override
        public void map(Object key, Text value, Context ctx)
                throws IOException, InterruptedException {
            String line = value.toString();
            if (line.startsWith("order_id")) return;
            String[] f = line.split(",");
            if (f.length <= COL_PRICE) return;
            try {
                category.set(f[COL_CATEGORY].trim());
                price.set(Double.parseDouble(f[COL_PRICE].trim()));
                ctx.write(category, price);
            } catch (NumberFormatException ignored) {}
        }
    }

    public static class RevenueByCategoryReducer
            extends Reducer<Text, DoubleWritable, Text, DoubleWritable> {

        private final DoubleWritable result = new DoubleWritable();

        @Override
        public void reduce(Text key, Iterable<DoubleWritable> values, Context ctx)
                throws IOException, InterruptedException {
            double sum = 0;
            for (DoubleWritable v : values) sum += v.get();
            result.set(Math.round(sum * 100.0) / 100.0);
            ctx.write(key, result);
        }
    }

    // ----------------------------------------------------------------
    // JOB 2 — Nombre de commandes par région client
    // ----------------------------------------------------------------

    public static class OrdersByRegionMapper
            extends Mapper<Object, Text, Text, IntWritable> {

        private static final IntWritable ONE = new IntWritable(1);
        private final Text region = new Text();

        @Override
        public void map(Object key, Text value, Context ctx)
                throws IOException, InterruptedException {
            String line = value.toString();
            if (line.startsWith("order_id")) return;
            String[] f = line.split(",");
            if (f.length <= COL_CUST_REGION) return;
            region.set(f[COL_CUST_REGION].trim());
            ctx.write(region, ONE);
        }
    }

    public static class OrdersByRegionReducer
            extends Reducer<Text, IntWritable, Text, IntWritable> {

        private final IntWritable result = new IntWritable();

        @Override
        public void reduce(Text key, Iterable<IntWritable> values, Context ctx)
                throws IOException, InterruptedException {
            int count = 0;
            for (IntWritable v : values) count += v.get();
            result.set(count);
            ctx.write(key, result);
        }
    }

    // ----------------------------------------------------------------
    // JOB 3 — Distribution des notes clients (1 à 5 étoiles)
    // ----------------------------------------------------------------

    public static class RatingDistributionMapper
            extends Mapper<Object, Text, IntWritable, IntWritable> {

        private static final IntWritable ONE   = new IntWritable(1);
        private final        IntWritable score = new IntWritable();

        @Override
        public void map(Object key, Text value, Context ctx)
                throws IOException, InterruptedException {
            String line = value.toString();
            if (line.startsWith("order_id")) return;
            String[] f = line.split(",");
            if (f.length <= COL_SCORE) return;
            try {
                score.set(Integer.parseInt(f[COL_SCORE].trim()));
                ctx.write(score, ONE);
            } catch (NumberFormatException ignored) {}
        }
    }

    public static class RatingDistributionReducer
            extends Reducer<IntWritable, IntWritable, IntWritable, IntWritable> {

        private final IntWritable result = new IntWritable();

        @Override
        public void reduce(IntWritable key, Iterable<IntWritable> values, Context ctx)
                throws IOException, InterruptedException {
            int count = 0;
            for (IntWritable v : values) count += v.get();
            result.set(count);
            ctx.write(key, result);
        }
    }

    // ----------------------------------------------------------------
    // JOB 4 — Tendance mensuelle du chiffre d'affaires
    // ----------------------------------------------------------------

    public static class MonthlyTrendMapper
            extends Mapper<Object, Text, Text, DoubleWritable> {

        private final Text           month = new Text();
        private final DoubleWritable price = new DoubleWritable();

        @Override
        public void map(Object key, Text value, Context ctx)
                throws IOException, InterruptedException {
            String line = value.toString();
            if (line.startsWith("order_id")) return;
            String[] f = line.split(",");
            if (f.length <= COL_DATE) return;
            try {
                month.set(f[COL_DATE].trim());
                price.set(Double.parseDouble(f[COL_PRICE].trim()));
                ctx.write(month, price);
            } catch (NumberFormatException ignored) {}
        }
    }

    public static class MonthlyTrendReducer
            extends Reducer<Text, DoubleWritable, Text, DoubleWritable> {

        private final DoubleWritable result = new DoubleWritable();

        @Override
        public void reduce(Text key, Iterable<DoubleWritable> values, Context ctx)
                throws IOException, InterruptedException {
            double sum = 0;
            for (DoubleWritable v : values) sum += v.get();
            result.set(Math.round(sum * 100.0) / 100.0);
            ctx.write(key, result);
        }
    }

    // ----------------------------------------------------------------
    // MAIN — dispatch selon le type de job
    // ----------------------------------------------------------------

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.err.println("Usage: EcommerceAnalysis <job> <input> <output>");
            System.err.println("  jobs disponibles : revenue_category | orders_region | ratings | monthly_trend");
            System.exit(1);
        }

        String jobType = args[0];
        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "ecommerce-" + jobType);
        job.setJarByClass(EcommerceAnalysis.class);
        FileInputFormat.addInputPath(job, new Path(args[1]));
        FileOutputFormat.setOutputPath(job, new Path(args[2]));

        switch (jobType) {
            case "revenue_category":
                job.setMapperClass(RevenueByCategoryMapper.class);
                job.setCombinerClass(RevenueByCategoryReducer.class);
                job.setReducerClass(RevenueByCategoryReducer.class);
                job.setOutputKeyClass(Text.class);
                job.setOutputValueClass(DoubleWritable.class);
                break;

            case "orders_region":
                job.setMapperClass(OrdersByRegionMapper.class);
                job.setCombinerClass(OrdersByRegionReducer.class);
                job.setReducerClass(OrdersByRegionReducer.class);
                job.setOutputKeyClass(Text.class);
                job.setOutputValueClass(IntWritable.class);
                break;

            case "ratings":
                job.setMapperClass(RatingDistributionMapper.class);
                job.setCombinerClass(RatingDistributionReducer.class);
                job.setReducerClass(RatingDistributionReducer.class);
                job.setOutputKeyClass(IntWritable.class);
                job.setOutputValueClass(IntWritable.class);
                break;

            case "monthly_trend":
                job.setMapperClass(MonthlyTrendMapper.class);
                job.setCombinerClass(MonthlyTrendReducer.class);
                job.setReducerClass(MonthlyTrendReducer.class);
                job.setOutputKeyClass(Text.class);
                job.setOutputValueClass(DoubleWritable.class);
                break;

            default:
                System.err.println("Job inconnu : " + jobType);
                System.exit(1);
        }

        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
