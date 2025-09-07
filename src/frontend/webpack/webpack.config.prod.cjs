const Webpack = require("webpack");
const { merge } = require("webpack-merge");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
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
    }),
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
        loader: "esbuild-loader",
        options: {
          // we can pass options as we like
          target: ["es2017"],
        },
      },
      {
        test: /\.s?css/i,
        use: [MiniCssExtractPlugin.loader, "css-loader", "postcss-loader", "sass-loader"],
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
