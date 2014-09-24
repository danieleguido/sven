'use strict';

describe('Service: concepts', function () {

  // load the service's module
  beforeEach(module('svenClientApp'));

  // instantiate service
  var concepts;
  beforeEach(inject(function (_concepts_) {
    concepts = _concepts_;
  }));

  it('should do something', function () {
    expect(!!concepts).toBe(true);
  });

});
