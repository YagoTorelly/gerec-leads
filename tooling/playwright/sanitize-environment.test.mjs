import assert from "node:assert/strict";
import test from "node:test";

import { withoutNoColor } from "./sanitize-environment.mjs";

test("cria um ambiente filho sem NO_COLOR sem mutar o ambiente de origem", () => {
  const sourceEnvironment = {
    FORCE_COLOR: "1",
    NO_COLOR: "1",
    PATH: "C:\\Windows",
  };

  const childEnvironment = withoutNoColor(sourceEnvironment);

  assert.deepEqual(childEnvironment, {
    FORCE_COLOR: "1",
    PATH: "C:\\Windows",
  });
  assert.deepEqual(sourceEnvironment, {
    FORCE_COLOR: "1",
    NO_COLOR: "1",
    PATH: "C:\\Windows",
  });
  assert.notStrictEqual(childEnvironment, sourceEnvironment);
});
