import express from "express";
import dotenv from "dotenv";
import swaggerJsdoc from "swagger-jsdoc";
import swaggerUi from "swagger-ui-express";
import authRoutes from "./routes/authRoutes";
import itemRoutes from "./routes/itemRoutes";

dotenv.config();

const app = express();
const port = process.env.port || 8080;
const swaggerDefinition = {
  openapi: "3.0.0",
  info: {
    title: "EDIMS API",
    version: "1.0.0",
  },
};

const options = {
  swaggerDefinition,
  apis: ["./src/routes/*.js"],
};

const swaggerSpec = swaggerJsdoc(options);
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));
app.use(express.json());
app.use("/auth", authRoutes);
app.use("/item", itemRoutes);

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
