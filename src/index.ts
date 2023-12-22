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
  components: {
    schemas: {
      User: {
        type: "object",
        properties: {
          username: {
            type: "string",
          },
          email: {
            type: "string",
            format: "email",
          },
          password: {
            type: "string",
            format: "password",
          },
        },
        required: ["username", "email", "password"],
      },
      UserWithoutPassword: {
        type: "object",
        properties: {
          id: {
            type: "integer",
            format: "int64",
          },
          username: {
            type: "string",
          },
          email: {
            type: "string",
            format: "email",
          },
        },
        required: ["id", "username", "email"],
      },
      LoginCredentials: {
        type: "object",
        properties: {
          email: {
            type: "string",
            format: "email",
          },
          password: {
            type: "string",
            format: "password",
          },
        },
        required: ["email", "password"],
      },
      Item: {
        type: "object",
        properties: {
          id: {
            type: "integer",
            format: "int64",
          },
          userid: {
            type: "integer",
            format: "int64",
          },
          name: {
            type: "string",
          },
          image: {
            type: "string",
          },
          category: {
            type: "string",
          },
          date: {
            type: "string",
          },
        },
        required: ["id", "userid", "name", "image", "category", "date"],
      },
    },
  },
};

const options = {
  swaggerDefinition,
  apis: ["./src/routes/*.ts"],
};

const swaggerSpec = swaggerJsdoc(options);
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));
app.use(express.json());
app.use("/auth", authRoutes);
app.use("/item", itemRoutes);

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
