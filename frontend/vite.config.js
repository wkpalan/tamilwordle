import { resolve } from "path";

module.exports = {
  base: "./",
  build: {
    outDir: "build",
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        // blogs: resolve(__dirname, "blogs/index.html"),
        // about: resolve(__dirname, "about/index.html"),
      },
    },
  },
};
