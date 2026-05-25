//VERSION=3
// PRE-HACKATHON FEASIBILITY SPIKE, DO NOT SUBMIT.
// Exploratory MNDWI only: (B03 - B11) / (B03 + B11).

function setup() {
  return {
    input: [{
      bands: ["B03", "B11", "SCL", "dataMask"]
    }],
    output: [
      {
        id: "mndwi",
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
  var denominator = samples.B03 + samples.B11;
  var value = valid && denominator !== 0 ? (samples.B03 - samples.B11) / denominator : 0;

  return {
    mndwi: [value],
    dataMask: [valid ? 1 : 0]
  };
}
