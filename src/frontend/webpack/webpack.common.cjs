const glob = require("glob");
const Path = require("path");
const { VueLoaderPlugin } = require("vue-loader");
const Dotenv = require("dotenv-webpack");
const { CleanWebpackPlugin } = require("clean-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");
const { WebpackAssetsManifest } = require("webpack-assets-manifest");
const { ProvidePlugin } = require("webpack");

const getEntryObject = () => {
  const entries = {};
  // for javascript/typescript entry file
  glob.sync(Path.join(__dirname, "../src/application/*.{js,ts}")).forEach((path) => {
    const name = Path.basename(path);
    const extension = Path.extname(path);
    const entryName = name.replace(extension, "");
    if (entryName in entries) {
      throw new Error(`Entry file conflict: ${entryName}`);
    }
    entries[entryName] = path;
  });
  return entries;
};

module.exports = {
  entry: {
    ...getEntryObject(),
    // Add a new entry point for ApexCharts and its Preline helper
    "apexcharts-helper": [
      Path.resolve(__dirname, "../node_modules/apexcharts/dist/apexcharts.min.js"),
      Path.resolve(__dirname, "../node_modules/@preline/helper-apexcharts/index.js"),
    ],
  },
  output: {
    path: Path.join(__dirname, "../build"),
    filename: "js/[name].js",
    publicPath: "/static/",
    assetModuleFilename: "[path][name][ext]",
  },
  optimization: {
    splitChunks: {
      chunks: "all",
    },
    runtimeChunk: "single",
  },
  plugins: [
    new VueLoaderPlugin(),
    new Dotenv({
      path: "./.env", // Path to .env file
      safe: false, // If true, load '.env.example' to verify the .env variables are all set
      systemvars: false, // If true, load all system environment variables
      silent: false, // If true, all warnings will be suppressed
      defaults: false, // If true, load '.env.defaults'
    }),
    new ProvidePlugin({
      process: "process/browser",
    }),
    new CleanWebpackPlugin(),
    new CopyWebpackPlugin({
      patterns: [{ from: Path.resolve(__dirname, "../vendors"), to: "vendors" }],
    }),
    new WebpackAssetsManifest({
      entrypoints: true,
      output: "manifest.json",
      writeToDisk: true,
      publicPath: true,
    }),
  ],
  resolve: {
    alias: {
      "~": Path.resolve(__dirname, "../src"),
    },
    fallback: {
      process: require.resolve("process/browser"),
    },
  },
  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: "vue-loader",
      },
      {
        test: /\.mjs$/,
        include: /node_modules/,
        type: "javascript/auto",
      },
      {
        test: /\.(ico|jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2)(\?.*)?$/,
        type: "asset",
      },
      {
        test: /\.worker\.js$/,
        use: {
          loader: "worker-loader",
          options: {
            worker: {
              target: "webworker", // Critical: Set worker target
            },
          },
        },
      },
    ],
  },
};
