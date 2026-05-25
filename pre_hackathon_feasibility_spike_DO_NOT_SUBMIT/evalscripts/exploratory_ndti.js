//VERSION=3
// PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
// Exploratory NDTI proxy only: (B04 - B03) / (B04 + B03).

function setup() {
  return {
    input: [{
      bands: ["B04", "B03", "SCL", "dataMask"]
    }],
    output: [
      {
        id: "ndti",
        bands: 1,
        sampleType: "FLOAT32"
      },
      {
        id: "dataMask",
        bands: 1
      }
    ]
  };
}

function isCloudOrShadow(scl) {
  return scl === 3 || scl === 8 || scl === 9 || scl === 10 || scl === 11;
}

function evaluatePixel(samples) {
  var valid = samples.dataMask === 1 && !isCloudOrShadow(samples.SCL);
  var denominator = samples.B04 + samples.B03;
  var value = valid && denominator !== 0 ? (samples.B04 - samples.B03) / denominator : 0;

  return {
    ndti: [value],
    dataMask: [valid ? 1 : 0]
  };
}
