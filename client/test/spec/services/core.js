'use strict';

describe('Service: core', function () {

  // load the service's module
  beforeEach(module('svenClientApp'));

  // instantiate service
  var core;
  beforeEach(inject(function (_core_) {
    core = _core_;
  }));

  it('should do something', function () {
    expect(!!core).toBe(true);
  });

});
