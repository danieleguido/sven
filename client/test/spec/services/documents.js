'use strict';

describe('Service: documents', function () {

  // load the service's module
  beforeEach(module('svenClientApp'));

  // instantiate service
  var documents;
  beforeEach(inject(function (_documents_) {
    documents = _documents_;
  }));

  it('should do something', function () {
    expect(!!documents).toBe(true);
  });

});
