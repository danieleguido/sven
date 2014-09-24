'use strict';

describe('Filter: tag', function () {

  // load the filter's module
  beforeEach(module('svenClientApp'));

  // initialize a new instance of the filter before each test
  var tag;
  beforeEach(inject(function ($filter) {
    tag = $filter('tag');
  }));

  it('should return the input prefixed with "tag filter:"', function () {
    var text = 'angularjs';
    expect(tag(text)).toBe('tag filter: ' + text);
  });

});
