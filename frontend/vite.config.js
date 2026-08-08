import { resolve } from "path";

const now = new Date();
const year = now.getFullYear();
const month = String(now.getMonth() + 1).padStart(2, "0");
const day = String(now.getDate()).padStart(2, "0");
const hours = String(now.getHours()).padStart(2, "0");
const mins = String(now.getMinutes()).padStart(2, "0");
const buildTimestamp = `v${year}.${month}.${day}-${hours}${mins}`;

module.exports = {
  base: "./",
  define: {
    __APP_VERSION__: JSON.stringify(buildTimestamp),
  },
  build: {
    outDir: "build",
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
      },
    },
  },
};

