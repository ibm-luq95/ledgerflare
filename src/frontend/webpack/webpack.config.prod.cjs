const Webpack = require("webpack");
const { merge } = require("webpack-merge");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const Path = require("path");
const common = require("./webpack.common.cjs");

module.exports = merge(common, {
  mode: "production",
  devtool: "source-map",
  bail: true,
  output: {
    filename: "js/[name].[chunkhash:8].js",
    chunkFilename: "js/[name].[chunkhash:8].chunk.js",
  },
  plugins: [
    new Webpack.DefinePlugin({
      "process.env.NODE_ENV": JSON.stringify("production"),
      // Vue 3 feature flags (prod)
      "__VUE_OPTIONS_API__": JSON.stringify(false), // ← Set to false if you use only Composition API
      "__VUE_PROD_DEVTOOLS__": JSON.stringify(false), // ← Disable in production
      "__VUE_PROD_HYDRATION_MISMATCH_DETAILS__": JSON.stringify(false),
    }),
    // new Webpack.DefinePlugin({
    //   "process.env.NODE_ENV": JSON.stringify("production"),
    // }),
    new MiniCssExtractPlugin({
      filename: "css/[name].[contenthash].css",
      chunkFilename: "css/[id].[contenthash].css",
    }),
  ],
  module: {
    rules: [
      // {
      //   test: /\.js$/,
      //   exclude: /node_modules/,
      //   use: "babel-loader",
      // },
      {
        test: /\.js$/,
        include: Path.resolve(__dirname, "../src"),
        resourceQuery: { not: [/vue/] }, // ← critical fix
        loader: "esbuild-loader",
        options: {
          target: ["es2017"],
        },
      },
      {
        test: /\.s?css/i,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          "postcss-loader",
          "sass-loader",
        ],
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
});
