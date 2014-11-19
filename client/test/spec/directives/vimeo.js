'use strict';

describe('Directive: vimeo', function () {

  // load the directive's module
  beforeEach(module('svenClientApp'));

  var element,
    scope;

  beforeEach(inject(function ($rootScope) {
    scope = $rootScope.$new();
  }));

  it('should make hidden element visible', inject(function ($compile) {
    element = angular.element('<vimeo></vimeo>');
    element = $compile(element)(scope);
    expect(element.text()).toBe('this is the vimeo directive');
  }));
});
