const Path = require("path");
const Webpack = require("webpack");
const { merge } = require("webpack-merge");
const StylelintPlugin = require("stylelint-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const ESLintPlugin = require("eslint-webpack-plugin");

const common = require("./webpack.common.cjs");

module.exports = merge(common, {
  target: "web",
  mode: "development",
  devtool: "inline-source-map",
  devServer: {
    hot: true,
    host: "0.0.0.0",
    port: 9091,
    headers: {
      "Access-Control-Allow-Origin": "*",
    },
    devMiddleware: {
      writeToDisk: true,
    },
  },
  output: {
    chunkFilename: "js/[name].chunk.js",
    clean: true,
  },
  plugins: [
    new Webpack.DefinePlugin({
      "process.env.NODE_ENV": JSON.stringify("development"),
      // Vue 3 compile-time feature flags (for esm-bundler build)
      "__VUE_OPTIONS_API__": JSON.stringify(true),
      "__VUE_PROD_DEVTOOLS__": JSON.stringify(true),
      "__VUE_PROD_HYDRATION_MISMATCH_DETAILS__": JSON.stringify(true),
    }),
    // new Webpack.DefinePlugin({
    // "process.env.NODE_ENV": JSON.stringify("development"),
    // }),
    new StylelintPlugin({
      files: Path.resolve(__dirname, "../src/**/*.s?(a|c)ss"),
    }),
    new ESLintPlugin({
      extensions: "js",
      emitWarning: true,
      files: Path.resolve(__dirname, "../src"),
    }),
    new MiniCssExtractPlugin({
      filename: "css/[name].css",
      chunkFilename: "css/[id].css",
    }),
  ],
  module: {
    rules: [
      {
        test: /\.html$/i,
        loader: "html-loader",
      },
      /* {
        test: /\.js$/,
        include: Path.resolve(__dirname, "../src"),
        loader: "babel-loader",
      }, */
      // ✅ FIXED JS RULE
      {
        test: /\.js$/,
        include: Path.resolve(__dirname, "../src"),
        resourceQuery: { not: [/vue/] }, // ← excludes Vue internal modules
        loader: "esbuild-loader",
        options: {
          target: ["es2017"],
        },
      },

      {
        test: /\.s?css$/i,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: "css-loader",
            options: {
              sourceMap: true,
            },
          },
          "postcss-loader",
        ],
      },
    ],
  },
});
