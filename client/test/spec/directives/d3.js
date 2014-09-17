'use strict';

describe('Directive: d3', function () {

  // load the directive's module
  beforeEach(module('svenClientApp'));

  var element,
    scope;

  beforeEach(inject(function ($rootScope) {
    scope = $rootScope.$new();
  }));

  it('should make hidden element visible', inject(function ($compile) {
    element = angular.element('<d3></d3>');
    element = $compile(element)(scope);
    expect(element.text()).toBe('this is the d3 directive');
  }));
});
